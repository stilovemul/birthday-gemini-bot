import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
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

    lines.append("\n💬 <i>Напишите название магазина или ресторана для поиска персональной скидки:</i>")
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

    lines.append("\n💬 <i>Напишите название платформы (Steam, Epic Games, PS5) для поиска раздач:</i>")
    return "\n".join(lines)


@router.message(Command("promos"))
@router.message(Command("games"))
@router.message(F.text.in_(["🎁 Промокоды & 🎮 Игры", "🍕 Промокоды на доставку", "🎮 Раздачи игр"]))
async def cmd_freebies_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍕 Промокоды на доставку еды", callback_data="mode_start_promos")],
            [InlineKeyboardButton(text="🎮 Бесплатные игры (EGS, Steam, GOG)", callback_data="mode_start_games")]
        ]
    )
    await message.answer(
        "🎁 <b>Радар халявы, промокодов и раздач игр:</b>\n\n"
        "Выберите раздел:\n"
        "• <b>Промокоды на еду</b> — Самокат, Купер, Яндекс Еда, ВкусВилл, Додо.\n"
        "• <b>Раздачи игр</b> — еженедельные 100% бесплатные игры в EGS и Steam.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@router.callback_query(F.data == "mode_start_promos")
async def cb_start_promos(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.promos_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id)
    text = format_promos_card(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Промокоды"), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "mode_start_games")
async def cb_start_games(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.games_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id)
    text = format_games_card(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Игры"), disable_web_page_preview=True)
    await callback.answer()


@router.message(ActiveModeStates.promos_mode)
async def handle_promos_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Промокоды» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id)
    reply = format_promos_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Промокоды"), disable_web_page_preview=True)


@router.message(ActiveModeStates.games_mode)
async def handle_games_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Игры» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id)
    reply = format_games_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Игры"), disable_web_page_preview=True)
