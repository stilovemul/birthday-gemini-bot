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


def get_ps5_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Распродажи PS Store", callback_data="ps5_filter_sales"),
                InlineKeyboardButton(text="🎁 Входят в PS Plus", callback_data="ps5_filter_plus")
            ],
            [
                InlineKeyboardButton(text="⚠️ Удалят из подписки", callback_data="ps5_filter_leaving"),
                InlineKeyboardButton(text="🔄 Полная сводка", callback_data="ps5_filter_all")
            ]
        ]
    )


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


def format_ps5_card(data: dict, filter_mode: str = "all", is_direct_query: bool = False) -> str:
    lines = []

    # Optional direct answer if user asked a specific question
    custom_ans = data.get("custom_answer")
    if is_direct_query and custom_ans and custom_ans.strip():
        lines.append(f"🤖 <b>Ответ на ваш вопрос:</b>\n{custom_ans.strip()}\n")

    # Header
    if filter_mode == "sales":
        lines.append("🏷 <b>🔥 Актуальные и ближайшие распродажи в PlayStation Store (PS5):</b>\n")
    elif filter_mode == "plus":
        lines.append("🎁 <b>Новинки подписки PlayStation Plus (Essential, Extra, Deluxe):</b>\n")
    elif filter_mode == "leaving":
        lines.append("⚠️ <b>Игры, которые скоро УДАЛЯТ из PlayStation Plus (Last Chance to Play):</b>\n")
    else:
        lines.append("🎮 <b>PlayStation 5 — Распродажи, PS Plus и игры на удаление:</b>\n")

    # 1. SALES SECTION
    if filter_mode in ["all", "sales"]:
        sales = data.get("sales", {})
        if sales:
            lines.append(f"🔥 <b>{sales.get('title', 'Распродажа в PS Store')}</b>")
            if sales.get("dates"):
                lines.append(f"📅 <b>Сроки проведения:</b> {sales.get('dates')}")
            if sales.get("description"):
                lines.append(f"💬 <i>{sales.get('description')}</i>")
            
            deals = sales.get("highlight_deals", [])
            if deals:
                lines.append("🕹 <b>Главные скидки на хиты PS5:</b>")
                for d in deals:
                    lines.append(f"   • <b>{d.get('game')}</b> — <code>{d.get('discount')}</code> ({d.get('note', '')})")
            lines.append("")

    # 2. PS PLUS ESSENTIAL (MONTHLY GAMES)
    if filter_mode in ["all", "plus"]:
        ess = data.get("ps_plus_essential", {})
        if ess:
            lines.append(f"🎁 <b>PS Plus Essential ({ess.get('period', 'Игры месяца')}):</b>")
            for g in ess.get("games", []):
                plat = f"[{g.get('platform', 'PS5')}]"
                genre = f"({g.get('genre', '')})" if g.get('genre') else ""
                lines.append(f"   • <b>{g.get('title')}</b> {plat} {genre}")
                if g.get("short_desc"):
                    lines.append(f"     └ <i>{g.get('short_desc')}</i>")
            lines.append("")

    # 3. PS PLUS EXTRA & DELUXE
    if filter_mode in ["all", "plus"]:
        extra = data.get("ps_plus_extra_deluxe", {})
        if extra:
            lines.append(f"🌟 <b>Каталог PS Plus Extra / Deluxe ({extra.get('period', 'Новинки')}):</b>")
            for g in extra.get("games", []):
                plat = f"[{g.get('platform', 'PS5')}]"
                genre = f"({g.get('genre', '')})" if g.get('genre') else ""
                lines.append(f"   • <b>{g.get('title')}</b> {plat} {genre}")
                if g.get("short_desc"):
                    lines.append(f"     └ <i>{g.get('short_desc')}</i>")
            lines.append("")

    # 4. LEAVING SOON (LAST CHANCE TO PLAY)
    if filter_mode in ["all", "leaving"]:
        leaving = data.get("leaving_soon", {})
        if leaving:
            lines.append(f"⚠️ <b>СКОРО УДАЛЯТ ИЗ ПОДПИСКИ (Extra / Deluxe):</b>")
            if leaving.get("leave_date"):
                lines.append(f"⏳ <b>Дата удаления из каталога:</b> <b>{leaving.get('leave_date')}</b>")
            for g in leaving.get("games", []):
                plat = f"[{g.get('platform', 'PS5')}]"
                lines.append(f"   ❌ <b>{g.get('title')}</b> {plat} — <i>{g.get('note', '')}</i>")
            if leaving.get("warning"):
                lines.append(f"\n🚨 <i>{leaving.get('warning')}</i>")
            lines.append("")

    # 5. TIP
    if data.get("ps5_tip") and filter_mode in ["all", "sales", "plus", "leaving"]:
        lines.append(f"{data['ps5_tip']}\n")

    lines.append("💬 <i>Вы в интерактивном режиме PS5. Спросите про любую игру, цены в Турции/Польше или воспользуйтесь кнопками ниже:</i>")
    return "\n".join(lines)


@router.message(Command("promos"))
@router.message(Command("games"))
@router.message(F.text.in_(["🎁 Промо & PS", "🎁 Промокоды & 🎮 Игры", "Промо & PS", "🍕 Промокоды на доставку", "🎮 Раздачи игр", "🎮 Игры PS5", "🎮 PlayStation 5"]))
async def cmd_freebies_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍕 Яндекс.Еда & Перекрёсток", callback_data="mode_start_promos")],
            [InlineKeyboardButton(text="🎮 PlayStation 5 (PS5 & PS Plus)", callback_data="mode_start_games")]
        ]
    )
    await message.answer(
        "🎁 <b>Персональный радар скидок, игр и распродаж:</b>\n\n"
        "• <b>Яндекс.Еда & Перекрёсток</b> — свежие промокоды на доставку еды и продуктов.\n"
        "• <b>PlayStation 5 (PS5 & PS Plus)</b> — распродажи PS Store, новинки PS Plus и игры, которые скоро удалят из подписки.",
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
    text = format_ps5_card(data, filter_mode="all")
    await callback.message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_ps5_inline_keyboard(),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.callback_query(F.data == "ps5_filter_sales")
async def cb_ps5_filter_sales(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query="актуальные распродажи и скидки в PS Store")
    text = format_ps5_card(data, filter_mode="sales")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("🔥 Сводка распродаж PS Store загружена!")


@router.callback_query(F.data == "ps5_filter_plus")
async def cb_ps5_filter_plus(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query="новинки игр PS Plus Essential и пополнения каталога Extra/Deluxe")
    text = format_ps5_card(data, filter_mode="plus")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("🎁 Новинки PS Plus загружены!")


@router.callback_query(F.data == "ps5_filter_leaving")
async def cb_ps5_filter_leaving(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query="игры которые скоро удалят из подписки PS Plus Extra Deluxe Last Chance to Play")
    text = format_ps5_card(data, filter_mode="leaving")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("⚠️ Список игр на удаление загружен!")


@router.callback_query(F.data == "ps5_filter_all")
async def cb_ps5_filter_all(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id)
    text = format_ps5_card(data, filter_mode="all")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("🔄 Полная сводка обновлена!")


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
    reply = format_ps5_card(data, filter_mode="all", is_direct_query=True)
    await message.answer(
        reply,
        parse_mode=ParseMode.HTML,
        reply_markup=get_ps5_inline_keyboard(),
        disable_web_page_preview=True
    )
