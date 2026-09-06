import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command

from core.keyboards import get_main_menu
from core.config import MSK_TZ
from datetime import datetime
from modules.morning_digest.digest import generate_morning_digest
from modules.morning_digest.holidays import get_today_holidays, MONTHS_GEN_RU, DAYS_RU

logger = logging.getLogger("MorningDigestHandler")
router = Router(name="morning_digest")


@router.message(Command("digest"))
@router.message(Command("morning"))
@router.message(F.text.in_(["🌅 Дайджест", "🌅 Утренний дайджест", "Дайджест", "Утренний дайджест", "📰 Сводка на день"]))
async def cmd_morning_digest(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    digest_text = await generate_morning_digest(user_id)
    await message.answer(digest_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=get_main_menu())


@router.message(Command("holidays"))
@router.message(Command("prazdnik"))
@router.message(Command("prazdniki"))
@router.message(F.text.func(lambda text: bool(text and text.strip().lower() in [
    "праздники", "праздники сегодня", "какие сегодня праздники", "какой сегодня праздник",
    "🎉 праздники", "🎉 праздники сегодня", "праздник сегодня", "какой праздник сегодня",
    "праздник дня", "сегодняшние праздники"
])))
async def cmd_today_holidays(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    now = datetime.now(MSK_TZ)
    weekday = DAYS_RU.get(now.weekday(), "")
    d_str = f"{now.day} {MONTHS_GEN_RU[now.month]} {now.year} г., {weekday}"
    
    holidays_text = await get_today_holidays(now)
    
    card = (
        f"🎉 <b>Праздники на сегодня</b> ✨\n"
        f"📅 <i>{d_str}</i>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        f"{holidays_text}\n\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"💡 <i>Полную утреннюю сводку (погода, ДР, умный дом) можно открыть кнопкой «🌅 Дайджест».</i>"
    )
    
    inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🌅 Открыть полный дайджест", callback_data="open_full_digest")]
    ])
    
    await message.answer(card, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=inline_kb)


@router.callback_query(F.data == "open_full_digest")
async def cb_open_full_digest(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    digest_text = await generate_morning_digest(user_id)
    await callback.message.answer(digest_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=get_main_menu())

