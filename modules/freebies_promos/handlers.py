import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.freebies_promos.promos import get_curated_delivery_promos
from modules.freebies_promos.games_freebies import get_active_games_freebies

logger = logging.getLogger("FreebiesHandlers")
router = Router(name="freebies_promos")


def format_promos_card(data: dict) -> str:
    lines = [
        "🍕 <b>Радар скидок и промокодов на доставку еды:</b>\n"
    ]
    for s in data.get("services", []):
        lines.append(
            f"🛒 <b>{s.get('name')}</b> — <code>{s.get('code')}</code> (<b>{s.get('discount')}</b>)\n"
            f"   └ <i>{s.get('condition')}</i>"
        )

    if data.get("lifehack"):
        lines.append(f"\n{data['lifehack']}")

    return "\n".join(lines)


def format_games_card(data: dict) -> str:
    lines = [
        "🎮 <b>Мониторинг бесплатных раздач игр (100% Free):</b>\n"
    ]
    for g in data.get("free_games", []):
        lines.append(
            f"🕹 <b>{g.get('platform')}</b>: <b>{g.get('title')}</b>\n"
            f"   └ 🏷 <b>{g.get('original_price')}</b>\n"
            f"   └ 💬 <i>{g.get('description')}</i>\n"
            f"   └ 🔗 <a href='{g.get('link')}'>Забрать в магазине</a>\n"
        )

    if data.get("gamer_tip"):
        lines.append(f"\n{data['gamer_tip']}")

    return "\n".join(lines)


@router.message(Command("promos"))
@router.message(F.text.in_(["🍕 Промокоды на доставку", "🍕 Промокоды", "🍕 Скидки на еду"]))
async def cmd_promos(message: types.Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id)
    text = format_promos_card(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить промокоды", callback_data="freebie_refresh_promos")],
            [InlineKeyboardButton(text="🎮 Бесплатные игры", callback_data="freebie_show_games")]
        ]
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)


@router.message(Command("games"))
@router.message(Command("freebies"))
@router.message(F.text.in_(["🎮 Раздачи игр", "🎮 Бесплатные игры", "🎮 Игры халява"]))
async def cmd_games(message: types.Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id)
    text = format_games_card(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить раздачи", callback_data="freebie_refresh_games")],
            [InlineKeyboardButton(text="🍕 Промокоды на еду", callback_data="freebie_show_promos")]
        ]
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data == "freebie_refresh_promos")
async def cb_refresh_promos(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id)
    text = format_promos_card(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить промокоды", callback_data="freebie_refresh_promos")],
            [InlineKeyboardButton(text="🎮 Бесплатные игры", callback_data="freebie_show_games")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "freebie_refresh_games")
@router.callback_query(F.data == "freebie_show_games")
async def cb_show_games(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id)
    text = format_games_card(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить раздачи", callback_data="freebie_refresh_games")],
            [InlineKeyboardButton(text="🍕 Промокоды на еду", callback_data="freebie_show_promos")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "freebie_show_promos")
async def cb_show_promos(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id)
    text = format_promos_card(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить промокоды", callback_data="freebie_refresh_promos")],
            [InlineKeyboardButton(text="🎮 Бесплатные игры", callback_data="freebie_show_games")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()
