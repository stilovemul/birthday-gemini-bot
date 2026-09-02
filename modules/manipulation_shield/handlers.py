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
from modules.manipulation_shield.analyzer import analyze_manipulation

logger = logging.getLogger("ManipulationShieldHandlers")
router = Router(name="manipulation_shield")


def get_shield_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛡 Разобрать ещё сообщение", callback_data="shield_new_analysis"),
                InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("manipulation"))
@router.message(Command("shield"))
@router.message(F.text.in_(["🛡 Манипуляции", "🛡 Анти-Манипулятор", "🛡 Деконструктор манипуляций", "Манипуляции", "Анти-Манипулятор"]))
async def cmd_manipulation_shield(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.manipulation_shield_mode)
    text = (
        "🛡 <b>Деконструктор манипуляций & Защита личных границ:</b>\n\n"
        "Пришлите <b>текст сомнительного сообщения</b> или <b>СКРИНШОТ переписки</b> (от начальника, клиента, токсичного знакомого, партнера).\n\n"
        "🔍 <b>Что сделает бот:</b>\n"
        "• Вскроет скрытые приемы (газлайтинг, чувство вины, пассивная агрессия, ложная срочность).\n"
        "• Объяснит <b>истинный мотив</b> собеседника.\n"
        "• Даст <b>3 готовых варианта ответа</b> (Дипломатичный, Жесткий щит, Остроумный).\n\n"
        "💬 <i>Отправьте текст или скриншот переписки:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Анти-Манипулятор"))


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_shield(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏁 <b>Режим «Анти-Манипулятор» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )
    await callback.answer("Вы вышли в главное меню")


@router.callback_query(F.data == "shield_new_analysis")
async def cb_shield_new(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.manipulation_shield_mode)
    await callback.message.answer(
        "💬 <b>Отправьте текст или скриншот нового сообщения для деконструкции:</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.manipulation_shield_mode, F.photo)
async def handle_manipulation_photo(message: types.Message, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_bytes_io = await message.bot.download_file(file_info.file_path)
    image_bytes = file_bytes_io.read()

    result = await analyze_manipulation(message.from_user.id, text="Скриншот переписки", image_bytes=image_bytes)
    await _send_shield_result(message, result)


@router.message(ActiveModeStates.manipulation_shield_mode, F.text)
async def handle_manipulation_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Анти-Манипулятор» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    result = await analyze_manipulation(message.from_user.id, raw_text)
    await _send_shield_result(message, result)


async def _send_shield_result(message: types.Message, result: dict):
    score = html.escape(str(result.get("manipulation_score", "70%")))
    badge = html.escape(str(result.get("status_badge", "Скрытое давление")))
    tactics = result.get("tactics_detected", [])
    tactics_str = "\n".join(f"  • {html.escape(str(t))}" for t in tactics) if tactics else "  • Скрытое давление"
    agenda = html.escape(str(result.get("hidden_agenda", "")))
    diplomatic = html.escape(str(result.get("diplomatic_reply", "")))
    firm = html.escape(str(result.get("firm_shield_reply", "")))
    witty = html.escape(str(result.get("witty_counter_reply", "")))

    card = (
        f"🛡 <b>РАЗБОР МАНИПУЛЯЦИЙ В ПЕРЕПИСКЕ:</b>\n\n"
        f"📊 <b>Индекс давления:</b> <b>{score}</b> ({badge})\n\n"
        f"🚩 <b>Обнаруженные тактики:</b>\n{tactics_str}\n\n"
        f"🎭 <b>Истинный мотив собеседника:</b>\n<i>«{agenda}»</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>ВАРИАНТЫ ОТВЕТОВ ДЛЯ КОПИРОВАНИЯ:</b>\n\n"
        f"🤝 <b>1. Дипломатичный (Конструктив + Границы):</b>\n"
        f"<code>{diplomatic}</code>\n\n"
        f"⚔️ <b>2. Жесткий щит (Без оправданий):</b>\n"
        f"<code>{firm}</code>\n\n"
        f"🎭 <b>3. Остроумный (Сбить спесь):</b>\n"
        f"<code>{witty}</code>"
    )

    await message.answer(card, parse_mode=ParseMode.HTML, reply_markup=get_shield_keyboard())
