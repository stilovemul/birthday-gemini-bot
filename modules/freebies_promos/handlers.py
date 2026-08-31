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
        "🍕 <b>Промокоды: Яндекс.Еда & Перекрёсток Доставка:</b>\n"
    ]
    for s in data.get("services", []):
        lines.append(
            f"🛒 <b>{s.get('name')}</b>\n"
            f"   └ 🏷 <b>{s.get('discount')}</b> | Промокод: <code>{s.get('code')}</code>\n"
            f"   └ 💬 <i>{s.get('condition')}</i>\n"
        )

    if data.get("lifehack"):
        lines.append(f"{data['lifehack']}")

    lines.append("\n💬 <i>Вы в режиме промокодов. Напишите, на что именно нужен купон (рестораны, кулинария, магазины) или завершите режим кнопкой ниже.</i>")
    return "\n".join(lines)


def format_ps5_card(data: dict) -> str:
    lines = [
        "🎮 <b>PlayStation 5 (PS5) — Раздачи, PS Plus & Скидки:</b>\n"
    ]
    for g in data.get("ps5_deals", []):
        lines.append(
            f"<b>{g.get('category')}</b>\n"
            f"🕹 <b>{g.get('title')}</b> — <b>{g.get('price')}</b>\n"
            f"   └ 💬 <i>{g.get('description')}</i>\n"
            f"   └ 🔗 <a href='{g.get('link')}'>Открыть в PlayStation Store</a>\n"
        )

    if data.get("ps5_tip"):
        lines.append(f"{data['ps5_tip']}")

    lines.append("\n💬 <i>Вы в режиме PS5. Спросите про любую игру, статус PS Plus или цены в турецком/польском регионе!</i>")
    return "\n".join(lines)


@router.message(Command("promos"))
@router.message(Command("games"))
@router.message(F.text.in_(["🎁 Промокоды & 🎮 Игры", "🍕 Промокоды на доставку", "🎮 Раздачи игр", "🎮 Игры PS5", "🎮 PlayStation 5"]))
async def cmd_freebies_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍕 Яндекс.Еда & Перекрёсток", callback_data="mode_start_promos")],
            [InlineKeyboardButton(text="🎮 PlayStation 5 (PS5 & PS Plus)", callback_data="mode_start_games")]
        ]
    )
    await message.answer(
        "🎁 <b>Персональный радар скидок и игр:</b>\n\n"
        "• <b>Яндекс.Еда & Перекрёсток</b> — свежие промокоды на доставку еды и продуктов.\n"
        "• <b>PlayStation 5 (PS5)</b> — ежемесячные раздачи PS Plus, топ Free-to-Play игр и распродажи PS Store.",
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
    text = format_ps5_card(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("PlayStation 5"), disable_web_page_preview=True)
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
    data = await get_curated_delivery_promos(user_id, query=text)
    reply = format_promos_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Промокоды"), disable_web_page_preview=True)


@router.message(ActiveModeStates.games_mode)
async def handle_games_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «PlayStation 5» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query=text)
    reply = format_ps5_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("PlayStation 5"), disable_web_page_preview=True)
