import html
import io
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.ai_humanizer.humanizer import humanize_ai_text
from modules.voice_assistant.transcriber import transcribe_audio_gemini

logger = logging.getLogger("AIHumanizerHandlers")
router = Router(name="ai_humanizer")


def get_humanizer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Очеловечить ещё текст", callback_data="hum_new_text"),
                InlineKeyboardButton(text="🚪 В главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("humanize"))
@router.message(Command("anti_ai"))
@router.message(Command("text_ai"))
@router.message(Command("humanizer"))
@router.message(F.text.in_([
    "✍️ Текст AI", "✍️ Очеловечить", "✍️ Очеловечиватель",
    "Текст AI", "Очеловечить", "Очеловечиватель", "Детектор ИИ",
    "AI Humanizer", "Очеловечивание", "Анти-ИИ", "Очеловечить текст"
]))
async def cmd_ai_humanizer(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.ai_humanizer_mode)
    text = (
        "✍️ <b>Детектор ИИ и Очеловечиватель текстов (AI Humanizer):</b>\n\n"
        "Пришлите любой текст (статью, эссе, пост, поздравление, письмо, ответ нейросети) или <b>надиктуйте голосом</b> / кружочком 🎙\n\n"
        "🔍 <b>Что сделает бот:</b>\n"
        "• Измерит процент роботизированности (0–100%) и найдет маркеры ИИ.\n"
        "• Перепишет в <b>Живой авторский/экспертный стиль</b> (проходит любые AI-детекторы).\n"
        "• Сделает <b>Разговорный вариант</b> для Telegram-постов и живых диалогов.\n"
        "• Подготовит <b>Лаконичный панч</b> без воды.\n\n"
        "💬 <i>Отправьте текст или голосовое сообщение для очеловечивания:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Очеловечиватель"))


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_humanizer(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏁 <b>Режим «Очеловечиватель» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )
    await callback.answer("Вы вышли в главное меню")


@router.callback_query(F.data == "hum_new_text")
async def cb_humanizer_new(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.ai_humanizer_mode)
    await callback.message.answer(
        "💬 <b>Отправьте следующий текст или надиктуйте голосом:</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.ai_humanizer_mode, F.voice | F.video_note | F.audio)
async def handle_humanizer_voice(message: types.Message, state: FSMContext):
    """Handles voice messages and video notes in AI Humanizer mode."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    file_id = None
    mime_type = "audio/ogg"
    if message.voice:
        file_id = message.voice.file_id
        mime_type = "audio/ogg"
    elif message.video_note:
        file_id = message.video_note.file_id
        mime_type = "video/mp4"
    elif message.audio:
        file_id = message.audio.file_id
        mime_type = message.audio.mime_type or "audio/mp3"

    if not file_id:
        await message.answer("⚠️ Не удалось прочитать аудиозапись.", reply_markup=get_mode_keyboard("Очеловечиватель"))
        return

    try:
        file_info = await message.bot.get_file(file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file_info.file_path, destination=buf)
        audio_bytes = buf.getvalue()
        
        recognized_text = await transcribe_audio_gemini(audio_bytes, mime_type=mime_type)
        if not recognized_text:
            await message.answer("⚠️ Не удалось распознать речь. Попробуйте отправить текст.", reply_markup=get_mode_keyboard("Очеловечиватель"))
            return
            
        await message.answer(f"🎙 <b>Распознанный текст:</b>\n«<i>{html.escape(recognized_text)}</i>»", parse_mode=ParseMode.HTML)
        await _process_humanizer_text(message, recognized_text)
    except Exception as e:
        logger.error(f"Error in humanizer voice handler: {e}")
        await message.answer("⚠️ Ошибка при обработке аудио. Отправьте текст сообщением.", reply_markup=get_mode_keyboard("Очеловечиватель"))


@router.message(ActiveModeStates.ai_humanizer_mode, F.text)
async def handle_humanizer_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Очеловечиватель» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await _process_humanizer_text(message, raw_text)


async def _process_humanizer_text(message: types.Message, text: str):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    result = await humanize_ai_text(message.from_user.id, text)

    score = html.escape(str(result.get("ai_percentage", "70%")))
    verdict = html.escape(str(result.get("verdict", "🟡 Текст обработан нейросетью")))
    markers = result.get("ai_markers_found", [])
    
    markers_lines = []
    for m in markers[:4]:
        markers_lines.append(f"• <i>{html.escape(str(m))}</i>")
    markers_formatted = "\n".join(markers_lines) if markers_lines else "• <i>Шаблоны синтаксиса ИИ</i>"

    expert = html.escape(str(result.get("expert_humanized", "")))
    casual = html.escape(str(result.get("casual_humanized", "")))
    punchy = html.escape(str(result.get("punchy_humanized", "")))
    changes = html.escape(str(result.get("changes_summary", "")))

    response = (
        f"📊 <b>Аудит текста:</b> 🤖 <b>{score} ИИ</b> — {verdict}\n\n"
        f"🚩 <b>Маркеры робота:</b>\n{markers_formatted}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>1. ЖИВОЙ ЭКСПЕРТНЫЙ ВАРИАНТ (Авторский):</b>\n\n"
        f"{expert}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"☕️ <b>2. РАЗГОВОРНЫЙ ВАРИАНТ (Для постов & людей):</b>\n\n"
        f"{casual}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>3. ЛАКОНИЧНЫЙ ПАНЧ (Без воды):</b>\n\n"
        f"{punchy}\n\n"
        f"🛠 <b>Что вычищено:</b> <i>{changes}</i>"
    )

    # In case the message is extra long, Telegram limit is 4096 characters
    if len(response) > 4000:
        # Send in two parts
        part1 = (
            f"📊 <b>Аудит текста:</b> 🤖 <b>{score} ИИ</b> — {verdict}\n\n"
            f"🚩 <b>Маркеры робота:</b>\n{markers_formatted}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <b>1. ЖИВОЙ ЭКСПЕРТНЫЙ ВАРИАНТ:</b>\n\n"
            f"{expert}"
        )
        part2 = (
            "━━━━━━━━━━━━━━━━━━━\n"
            f"☕️ <b>2. РАЗГОВОРНЫЙ ВАРИАНТ:</b>\n\n"
            f"{casual}\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"⚡️ <b>3. ЛАКОНИЧНЫЙ ПАНЧ:</b>\n\n"
            f"{punchy}\n\n"
            f"🛠 <b>Что вычищено:</b> <i>{changes}</i>"
        )
        await message.answer(part1, parse_mode=ParseMode.HTML)
        await message.answer(part2, parse_mode=ParseMode.HTML, reply_markup=get_humanizer_keyboard())
    else:
        await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=get_humanizer_keyboard())
