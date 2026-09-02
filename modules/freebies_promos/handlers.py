import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.freebies_promos.promos import get_curated_delivery_promos
from modules.freebies_promos.games_freebies import get_active_games_freebies

logger = logging.getLogger("FreebiesHandlers")
router = Router(name="freebies_promos")


def get_promos_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍕 Яндекс.Еда & Лавка", callback_data="pr_preset_yandex"),
                InlineKeyboardButton(text="🛍 Купер & Самокат", callback_data="pr_preset_kuper")
            ],
            [
                InlineKeyboardButton(text="🍕 Додо, Токио & Рестораны", callback_data="pr_preset_dodo"),
                InlineKeyboardButton(text="🛒 ВкусВилл & Перекрёсток", callback_data="pr_preset_stores")
            ],
            [
                InlineKeyboardButton(text="💄 Золотое Яблоко & Ozon", callback_data="pr_preset_shops"),
                InlineKeyboardButton(text="🍔 Бургер Кинг & Вкусно и точка", callback_data="pr_preset_fastfood")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def format_promos_card(data: dict) -> str:
    title = html.escape(str(data.get("target_title", "Промокоды и Скидки")))
    cat_type = html.escape(str(data.get("category_type", "Скидки")))
    codes = data.get("active_codes", [])
    combos = html.escape(str(data.get("secret_combos", "")))
    bank = html.escape(str(data.get("bank_cashback_perks", "")))
    tip = html.escape(str(data.get("pro_saving_tip", "")))

    lines = [
        f"🎁 <b>{title.upper()}</b> <i>({cat_type})</i>\n",
        "🏷 <b>РАБОЧИЕ ПРОМОКОДЫ:</b>"
    ]

    for idx, c in enumerate(codes, 1):
        code_val = html.escape(str(c.get("code", "")))
        discount = html.escape(str(c.get("discount", "")))
        cond = html.escape(str(c.get("condition", "")))
        aud = html.escape(str(c.get("target_audience", "Все клиенты")))

        lines.append(
            f"<b>{idx}. 🎟 Промокод:</b> <code>{code_val}</code>\n"
            f"   └ 💰 <b>Выгода:</b> <b>{discount}</b>\n"
            f"   └ 👥 <b>Для кого:</b> {aud}\n"
            f"   └ 📋 <b>Условия:</b> <i>{cond}</i>\n"
        )

    if combos:
        lines.append(f"🍔 <b>Секретные комбо и акции:</b>\n{combos}\n")

    if bank:
        lines.append(f"💳 <b>Кэшбэк банков и баллы:</b>\n{bank}\n")

    if tip:
        lines.append(f"💡 <b>Лайфхак максимальной экономии:</b>\n<i>{tip}</i>\n")

    lines.append("💬 <i>Напишите название ЛЮБОГО ресторана, доставки или магазина (например: «промокод на доставку из Frank», «скидка Спортмастер», «Купер на первый заказ»):</i>")
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


@router.message(Command("promos"))
@router.message(Command("games"))
@router.message(F.text.in_(["🎁 Промо & PS", "🎁 Промокоды & 🎮 Игры", "Промо & PS", "🍕 Промокоды на доставку", "🎮 Раздачи игр", "🎮 Игры PS5", "🎮 PlayStation 5", "Промокоды", "Скидки"]))
async def cmd_freebies_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍕 Промокоды (Еда, Рестораны & Магазины)", callback_data="mode_start_promos")],
            [InlineKeyboardButton(text="🎮 PlayStation 5 (PS5 & PS Plus)", callback_data="mode_start_games")]
        ]
    )
    await message.answer(
        "🎁 <b>Персональный радар промокодов, скидок и PlayStation:</b>\n\n"
        "• 🍕 <b>Промокоды на доставку и магазины</b> — Яндекс.Еда, Купер, Самокат, Додо, рестораны, маркетплейсы (Ozon, WB, Золотое Яблоко).\n"
        "• 🎮 <b>PlayStation 5 (PS5 & PS Plus)</b> — распродажи PS Store, новинки PS Plus и игры на удаление.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@router.callback_query(F.data == "mode_start_promos")
async def cb_start_promos(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.promos_mode)
    user_id = callback.from_user.id
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id, "Яндекс.Еда, Купер, Самокат и популярные рестораны")
    text = format_promos_card(data)
    await callback.message.answer(
        "🎁 <b>Режим поиска промокодов и скидок активирован!</b>\n\n"
        "💡 <i>Вы можете нажать кнопку ниже или написать в чат ЛЮБОЙ запрос:</i>\n"
        "• <i>«промокод на доставку из ресторана Франк»</i>\n"
        "• <i>«промокод на доставку яндекс еда»</i>\n"
        "• <i>«скидка в золотом яблоке или спортмастере»</i>\n"
        "• <i>«купон на первый заказ купер»</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_mode_keyboard("Промокоды")
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_promos_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("pr_preset_"))
async def cb_promos_preset(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.promos_mode)
    preset_key = callback.data.replace("pr_preset_", "")
    user_id = callback.from_user.id
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    presets = {
        "yandex": "Яндекс Еда и Яндекс Лавка (первый заказ и повторные заказы)",
        "kuper": "Купер (СберМаркет) и Самокат (доставка продуктов и готовой еды)",
        "dodo": "Додо Пицца, Токио Сити, Bahroma, Суши Wok и доставка из ресторанов",
        "stores": "ВкусВилл и Перекрёсток Доставка (Шеф Перекресток, сервис Пакет)",
        "shops": "Золотое Яблоко, ЛЭТУАЛЬ, Ozon, Wildberries и Мегамаркет",
        "fastfood": "Бургер Кинг, Вкусно и точка, Ростикс KFC и авто-кафе"
    }
    q = presets.get(preset_key, "Яндекс Еда и доставка продуктов")
    await callback.answer(f"Ищу промокоды: {q[:25]}...")
    data = await get_curated_delivery_promos(user_id, query=q)
    text = format_promos_card(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_promos_inline_keyboard(), disable_web_page_preview=True)


@router.callback_query(F.data == "mode_start_games")
async def cb_start_games(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.games_mode)
    user_id = callback.from_user.id
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
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
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query="актуальные распродажи и скидки в PS Store")
    text = format_ps5_card(data, filter_mode="sales")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("🔥 Сводка распродаж PS Store загружена!")


@router.callback_query(F.data == "ps5_filter_plus")
async def cb_ps5_filter_plus(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query="новинки игр PS Plus Essential и пополнения каталога Extra/Deluxe")
    text = format_ps5_card(data, filter_mode="plus")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("🎁 Новинки PS Plus загружены!")


@router.callback_query(F.data == "ps5_filter_leaving")
async def cb_ps5_filter_leaving(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id, query="игры которые скоро удалят из подписки PS Plus Extra Deluxe Last Chance to Play")
    text = format_ps5_card(data, filter_mode="leaving")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("⚠️ Список игр на удаление загружен!")


@router.callback_query(F.data == "ps5_filter_all")
async def cb_ps5_filter_all(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_active_games_freebies(user_id)
    text = format_ps5_card(data, filter_mode="all")
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_ps5_inline_keyboard(), disable_web_page_preview=True)
    await callback.answer("🔄 Полная сводка обновлена!")


@router.message(ActiveModeStates.promos_mode, F.text)
async def handle_promos_dialog(message: types.Message, state: FSMContext):
    raw_text = message.text.strip() if message.text else ""
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Промокоды» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_curated_delivery_promos(user_id, query=raw_text)
    reply = format_promos_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_promos_inline_keyboard(), disable_web_page_preview=True)


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
