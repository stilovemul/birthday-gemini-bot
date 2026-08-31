import re
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.anti_spam_guard.checker import check_phone_number_reputation

logger = logging.getLogger("AntiSpamHandlers")
router = Router(name="anti_spam_guard")


def format_spam_card(data: dict) -> str:
    score = data.get("spam_score", 0)
    if score >= 70:
        bar = "🔴 <b>КРИТИЧЕСКИЙ РИСК</b>"
    elif score >= 40:
        bar = "🟡 <b>СРЕДНИЙ РИСК</b>"
    else:
        bar = "🟢 <b>НИЗКИЙ РИСК</b>"

    lines = [
        f"📵 <b>Отчет о проверке номера: {data.get('phone')}</b>\n",
        f"📡 <b>Оператор / Регион:</b> <i>{data.get('operator')}</i>",
        f"🛡 <b>Репутация:</b> {data.get('reputation')}",
        f"📊 <b>Индекс спама:</b> <b>{score}/100</b> ({bar})",
        f"📂 <b>Категория:</b> <i>{data.get('category')}</i>\n",
        f"👉 <b>Рекомендация:</b>\n<i>{data.get('recommendation')}</i>\n",
        "💬 <i>Режим проверки активен. Пришлите следующий номер или завершите режим кнопкой ниже.</i>"
    ]
    return "\n".join(lines)


@router.message(Command("num"))
@router.message(Command("spamcheck"))
@router.message(F.text.in_(["📵 Проверить номер", "📵 Антиспам", "📵 Чекер номеров"]))
async def cmd_check_number_menu(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.antispam_mode)
    text = (
        "📵 <b>Режим «Антиспам-чекер номеров» активирован!</b>\n\n"
        "Отправьте номер телефона в любом формате:\n"
        "👉 <code>+7 (921) 123-45-67</code>\n"
        "👉 <code>88124567890</code>\n"
        "👉 <i>«Кто звонил +79001112233?»</i>\n\n"
        "💡 <i>Бот проверит оператора, регион, спам-базы и уровень риска.</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Антиспам"))


@router.message(ActiveModeStates.antispam_mode)
async def handle_antispam_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Антиспам» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await check_phone_number_reputation(user_id, text)
    reply = format_spam_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Антиспам"))
