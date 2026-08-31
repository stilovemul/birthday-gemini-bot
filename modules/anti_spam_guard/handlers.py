import re
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
        "🔒 <i>Никогда не называйте коды из SMS и данные банковских карт незнакомым номерам!</i>"
    ]
    return "\n".join(lines)


@router.message(Command("num"))
@router.message(Command("spamcheck"))
@router.message(F.text.startswith("📵 Проверь номер"))
@router.message(F.text.startswith("/num"))
async def cmd_check_number(message: types.Message):
    user_id = message.from_user.id
    raw = message.text.replace("/num", "").replace("/spamcheck", "").replace("📵 Проверь номер", "").strip()
    if not raw:
        raw = "+7 (921) 999-00-11"

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await check_phone_number_reputation(user_id, raw)
    text = format_spam_card(data)
    await message.answer(text, parse_mode=ParseMode.HTML)
