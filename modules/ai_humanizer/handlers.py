import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.ai_humanizer.humanizer import humanize_ai_text

logger = logging.getLogger("AIHumanizerHandlers")
router = Router(name="ai_humanizer")


def get_humanizer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Очеловечить ещё текст", callback_data="hum_new_text"),
                InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("humanize"))
@router.message(Command("anti_ai"))
@router.message(F.text.in_(["✍️ Очеловечить", "✍️ Очеловечиватель", "✍️ Текст AI", "Очеловечить", "Очеловечиватель", "Детектор ИИ"]))
async def cmd_ai_humanizer(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.ai_humanizer_mode)
    text = (
        "✍️ <b>Детектор ИИ и Очеловечиватель текстов (AI Humanizer):</b>\n\n"
        "Пришлите любой текст, сгенерированный нейросетью (ChatGPT, Claude и др.) — статью, эссе, пост, письмо или ответ на вопрос.\n\n"
        "🔍 <b>Что сделает бот:</b>\n"
        "• Измерит процент роботизированности и найдет маркеры ИИ.\n"
        "• Перепишет в <b>Живой экспертный стиль</b> (проходит любые AI-детекторы).\n"
        "• Сделает <b>Разговорный вариант</b> для постов и переписок.\n\n"
        "💬 <i>Отправьте текст для очеловечивания:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Очеловечиватель"))


@router.callback_query(F.data == "hum_new_text")
async def cb_humanizer_new(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.ai_humanizer_mode)
    await callback.message.answer(
        "💬 <b>Отправьте следующий ИИ-текст для очеловечивания:</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.ai_humanizer_mode, F.text)
async def handle_humanizer_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if raw_text.startswith("/") or raw_text in ["🚪 Главное меню", "Главное меню", "Выход"]:
        await state.clear()
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    result = await humanize_ai_text(message.from_user.id, raw_text)

    score = html.escape(str(result.get("ai_percentage", "70%")))
    markers = result.get("ai_markers_found", [])
    markers_str = ", ".join(html.escape(str(m)) for m in markers) if markers else "Шаблоны синтаксиса"
    expert = html.escape(result.get("expert_humanized", ""))
    casual = html.escape(result.get("casual_humanized", ""))
    changes = html.escape(result.get("changes_summary", ""))

    response = (
        f"📊 <b>Анализ роботизированности:</b> 🤖 <b>{score} ИИ</b>\n"
        f"🚩 <b>Обнаруженные маркеры:</b> <i>{markers_str}</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>1. ЖИВОЙ ЭКСПЕРТНЫЙ ВАРИАНТ:</b>\n\n"
        f"{expert}\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"☕️ <b>2. РАЗГОВОРНЫЙ ВАРИАНТ (Для людей/постов):</b>\n\n"
        f"{casual}\n\n"
        f"🛠 <b>Что исправлено:</b> <i>{changes}</i>"
    )

    await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=get_humanizer_keyboard())
