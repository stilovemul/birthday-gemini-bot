import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command

from core.keyboards import get_main_menu
from modules.morning_digest.digest import generate_morning_digest

logger = logging.getLogger("MorningDigestHandler")
router = Router(name="morning_digest")


@router.message(Command("digest"))
@router.message(Command("morning"))
@router.message(F.text == "🌅 Утренний дайджест")
@router.message(F.text == "📰 Сводка на день")
async def cmd_morning_digest(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    digest_text = await generate_morning_digest(user_id)
    await message.answer(digest_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=get_main_menu())
