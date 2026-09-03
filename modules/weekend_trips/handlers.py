# -*- coding: utf-8 -*-
import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.weekend_trips.planner import plan_weekend_activity
from modules.weekend_trips.kids_planner import plan_kid_entertainment
from modules.weekend_trips.storage import get_user_last_trip, set_user_last_trip

logger = logging.getLogger("WeekendTripsHandlers")
router = Router(name="weekend_trips")


def get_weekend_keyboard() -> InlineKeyboardMarkup:
    """Стартовая клавиатура сценариев выходных."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👶 С малышом (1–3 года)", callback_data="wt_kids_menu"),
                InlineKeyboardButton(text="🚗 Авто-Роадтрип на 1-2 дня", callback_data="wt_roadtrip")
            ],
            [
                InlineKeyboardButton(text="🎪 Афиша и события СПб", callback_data="wt_afisha"),
                InlineKeyboardButton(text="🎲 Идеальный выходной сейчас", callback_data="wt_random")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_kids_menu_keyboard() -> InlineKeyboardMarkup:
    """Интерактивное меню развлечений строго для ребенка возрастом 1–3 года (малыша / тоддлера)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧸 Мягкие тоддлер-зоны (0–3)", callback_data="wt_kid_cat_play"),
                InlineKeyboardButton(text="🎭 Бэби-театры (1–3 года)", callback_data="wt_kid_cat_theater")
            ],
            [
                InlineKeyboardButton(text="🐑 Альпаки & Животные", callback_data="wt_kid_cat_zoo"),
                InlineKeyboardButton(text="🐠 Океанариум & Рыбки", callback_data="wt_kid_cat_ocean")
            ],
            [
                InlineKeyboardButton(text="💦 Тёплый бэби-бассейн", callback_data="wt_kid_cat_aqua"),
                InlineKeyboardButton(text="🌳 Парки под коляску", callback_data="wt_kid_cat_park")
            ],
            [
                InlineKeyboardButton(text="🎲 Топ-место для малыша 1–3 г", callback_data="wt_kid_random")
            ],
            [
                InlineKeyboardButton(text="🌲 К загородным маршрутам", callback_data="wt_to_routes"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_plan_result_keyboard(mode_type: str = "general") -> InlineKeyboardMarkup:
    """Клавиатура под готовым маршрутом: кнопка «Другой маршрут» на первом месте."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другой маршрут (Ещё)", callback_data=f"wt_another_{mode_type}")
            ],
            [
                InlineKeyboardButton(text="👶 С малышом 1–3 года", callback_data="wt_kids_menu"),
                InlineKeyboardButton(text="🚗 Роадтрип", callback_data="wt_roadtrip")
            ],
            [
                InlineKeyboardButton(text="🎪 Афиша СПб", callback_data="wt_afisha"),
                InlineKeyboardButton(text="🎲 Случайный", callback_data="wt_random")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_kid_result_keyboard(category: str = "all") -> InlineKeyboardMarkup:
    """Клавиатура под карточкой детского развлечения (строго для малыша 1–3 года)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другой вариант для малыша (Ещё)", callback_data=f"wt_kid_more_1-3_{category}")
            ],
            [
                InlineKeyboardButton(text="🧸 Тоддлер-зоны", callback_data="wt_kid_cat_play"),
                InlineKeyboardButton(text="🎭 Бэби-театры", callback_data="wt_kid_cat_theater")
            ],
            [
                InlineKeyboardButton(text="🐑 Альпаки & Фермы", callback_data="wt_kid_cat_zoo"),
                InlineKeyboardButton(text="🐠 Океанариум", callback_data="wt_kid_cat_ocean")
            ],
            [
                InlineKeyboardButton(text="💦 Тёплый бассейн", callback_data="wt_kid_cat_aqua"),
                InlineKeyboardButton(text="🌳 С коляской в парк", callback_data="wt_kid_cat_park")
            ],
            [
                InlineKeyboardButton(text="🌲 Загородные маршруты", callback_data="wt_to_routes"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("weekend"))
@router.message(Command("trips"))
@router.message(F.text.in_(["🌲 Выходные", "🌲 Выходные & Дети", "Сценарист выходных", "Роадтрип", "Афиша"]))
async def cmd_weekend_trips(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.weekend_planner_mode)
    text = (
        "🌲 <b>Сценарист выходных, Отдых с малышом 1–3 года & Авто-Роадтрипы:</b>\n\n"
        "Я составляю готовые сценарии отдыха под ключ с маршрутами, ценами, АЗС и детской инфраструктурой!\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Куда поехать с малышом 1.5–2 года на пару часов?»</i>\n"
        "• <i>«Тёплый бассейн или бэби-театр на подушках для ребенка 2 года»</i>\n"
        "• <i>«Парк с идеальной экотропой под детскую коляску в Курортном районе»</i>\n"
        "• <i>«Маршрут на машине в Карелию на 2 дня с красивыми видами»</i>\n"
        "• <i>«Что интересного проходит в эти выходные в СПб?»</i>\n\n"
        "💬 <i>Напишите ваш запрос или выберите кнопку:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Выходные"))
    await message.answer("👇 <b>Быстрый выбор сценария:</b>", parse_mode=ParseMode.HTML, reply_markup=get_weekend_keyboard())


@router.callback_query(F.data.startswith("wt_"))
async def cb_weekend_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.replace("wt_", "")
    await state.set_state(ActiveModeStates.weekend_planner_mode)

    # 1. Возврат к маршрутам
    if cat == "to_routes":
        await callback.answer()
        await callback.message.answer("🌲 <b>Загородные маршруты и роадтрипы:</b>", parse_mode=ParseMode.HTML, reply_markup=get_weekend_keyboard())
        return

    # 2. Детское меню для малыша 1–3 года
    if cat in ["kids", "kids_menu"]:
        await callback.answer()
        text = (
            "👶 <b>Развлечения с малышом 1–3 года в Санкт-Петербурге и ЛО:</b>\n\n"
            "Мягкие тоддлер-зоны 0–3, камерные бэби-театры на подушках, тёплые лягушатники (+32...+34°C), "
            "пушистые ручные альпаки, океанариум и живописные экотропы под детскую коляску!\n\n"
            "Все варианты подобраны <b>строго для возраста 1–3 года</b> — с комнатами матери и ребенка, "
            "пеленальными столиками, детскими стульчиками и удобным заездом с коляской.\n\n"
            "👇 <b>Выберите категорию для малыша:</b>"
        )
        await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_kids_menu_keyboard())
        return

    # 3. Подбор детского развлечения по возрасту (всегда 1–3 года)
    if cat.startswith("kid_age_"):
        await callback.answer("👶 Подбираю варианты для малыша 1–3 года...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        set_user_last_trip(callback.from_user.id, "Развлечения для малыша 1–3 года", "kids")
        res = await plan_kid_entertainment(callback.from_user.id, age_group="1-3", category="all")
        await render_kid_entertainment(callback.message, res, category="all")
        return

    # 4. Подбор развлечения для малыша по категории
    if cat.startswith("kid_cat_"):
        c_tag = cat.replace("kid_cat_", "")
        cat_names = {
            "play": "тоддлер-зону 0–3",
            "theater": "бэби-театр на подушках",
            "zoo": "ручных животных и альпак",
            "ocean": "океанариум и рыбок",
            "aqua": "тёплый бэби-бассейн",
            "park": "парк под коляску",
            "science": "бэби-театр"
        }
        if c_tag == "science":
            c_tag = "theater"
        await callback.answer(f"🔎 Ищу {cat_names.get(c_tag, 'развлечение для малыша')}...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        set_user_last_trip(callback.from_user.id, f"Развлечения для малыша 1–3 года: {c_tag}", "kids")
        res = await plan_kid_entertainment(callback.from_user.id, age_group="1-3", category=c_tag)
        await render_kid_entertainment(callback.message, res, category=c_tag)
        return

    # 5. Случайное топ-место для малыша 1–3 года
    if cat == "kid_random":
        await callback.answer("🎲 Подбираю топ-место для малыша 1–3 года...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        set_user_last_trip(callback.from_user.id, "Лучшее место для малыша 1–3 года в СПб", "kids")
        res = await plan_kid_entertainment(callback.from_user.id, age_group="1-3", category="all", is_another=True)
        await render_kid_entertainment(callback.message, res, category="all")
        return

    # 6. Кнопка «Другой вариант для малыша (Ещё)»
    if cat.startswith("kid_more_"):
        parts = cat.replace("kid_more_", "").split("_")
        c_tag = parts[-1] if len(parts) > 1 else "all"
        if c_tag in ["1-3", "4-6", "7-10", "11-14", "all"]:
            c_tag = "all"
        await callback.answer("🔄 Подбираю другое место для малыша...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        res = await plan_kid_entertainment(callback.from_user.id, age_group="1-3", category=c_tag, is_another=True)
        await render_kid_entertainment(callback.message, res, category=c_tag)
        return

    # 7. Другой загородный маршрут
    if cat.startswith("another"):
        await callback.answer("🔄 Подбираю новый маршрут...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        m_type = cat.replace("another_", "").replace("another", "").strip("_") or "general"
        last_info = get_user_last_trip(callback.from_user.id)
        query = last_info.get("query") or "Другой отличный сценарий проведения выходного дня"
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type=m_type, is_another=True)
        await render_weekend_plan(callback.message, res, mode_type=m_type)
        return

    # 8. Загородный роадтрип
    if cat == "roadtrip":
        await callback.answer("🚗 Составляю авто-маршрут...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        query = "Топ авто-роадтрип из СПб на 1-2 дня: Карелия, Ладога или живописные окрестности с лучшими смотровыми и кафе"
        set_user_last_trip(callback.from_user.id, query, "roadtrip")
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type="roadtrip", is_another=True)
        await render_weekend_plan(callback.message, res, mode_type="roadtrip")
        return

    # 9. Афиша СПб
    if cat == "afisha":
        await callback.answer("🎪 Ищу афишу и события...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        query = "Актуальная афиша событий в СПб на ближайшие выходные: фестивали, выставки, маркеты, мероприятия на крышах"
        set_user_last_trip(callback.from_user.id, query, "afisha")
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type="afisha", is_another=True)
        await render_weekend_plan(callback.message, res, mode_type="afisha")
        return

    # 10. Случайный идеальный выходной
    if cat == "random":
        await callback.answer("🎲 Генерирую идеальный выходной...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        query = "Лучший сценарий проведения выходного дня под текущий сезон"
        set_user_last_trip(callback.from_user.id, query, "general")
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type="general", is_another=True)
        await render_weekend_plan(callback.message, res, mode_type="general")
        return

    await callback.answer()


@router.message(ActiveModeStates.weekend_planner_mode, F.text)
async def handle_weekend_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Сценарист выходных» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    lower_text = raw_text.lower()
    another_triggers = [
        "другой", "еще", "ещё", "другой маршрут", "другой вариант",
        "еще вариант", "ещё вариант", "покажи еще", "покажи ещё",
        "давай другой", "не то", "следующий", "дальше", "поменяй", "другое"
    ]

    last_info = get_user_last_trip(message.from_user.id)
    last_mode = last_info.get("mode", "general")

    if lower_text in another_triggers:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        if last_mode == "kids":
            res = await plan_kid_entertainment(message.from_user.id, query="Другое развлечение для малыша 1-3 года", age_group="1-3", is_another=True)
            await render_kid_entertainment(message, res)
        else:
            query = last_info.get("query") or "Другой интересный сценарий проведения выходного дня"
            res = await plan_weekend_activity(message.from_user.id, query, mode_type=last_mode, is_another=True)
            await render_weekend_plan(message, res, mode_type=last_mode)
        return

    # Проверяем, относится ли запрос к детям / малышам
    kid_keywords = [
        "ребенок", "дети", "дочь", "сын", "детск", "детям", "малыш", "тоддлер",
        "зоопарк", "аквапарк", "океанариум", "игровая комната", "joki",
        "джоки", "кидбург", "мазапарк", "батут", "скалодром", "цирк",
        "аттракцион", "альпак", "зубр", "тесла", "лабиринтум", "коляск",
        "бэби", "беби", "театр", "сказк", "бабочк", "песочниц"
    ]

    is_kid_query = any(k in lower_text for k in kid_keywords)

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    if is_kid_query:
        # Для детей в модуле жестко зафиксирован возраст 1–3 года
        age_grp = "1-3"

        # Определяем категорию
        c_tag = "all"
        if any(w in lower_text for w in ["театр", "сказк", "спектакл", "кукол", "вильям", "karlsson", "подушк"]):
            c_tag = "theater"
        elif any(w in lower_text for w in ["океанариум", "рыб", "скат", "акул"]):
            c_tag = "ocean"
        elif any(w in lower_text for w in ["зоопарк", "животн", "альпак", "зубр", "кролик", "бабочк", "коз"]):
            c_tag = "zoo"
        elif any(w in lower_text for w in ["аквапарк", "бассейн", "водн", "лягушатник", "купаться"]):
            c_tag = "aqua"
        elif any(w in lower_text for w in ["парк", "коляск", "экотроп", "прогулк", "лес", "озеро", "пляж"]):
            c_tag = "park"
        elif any(w in lower_text for w in ["игров", "комнат", "лабиринт", "малышарик", "teika", "джоки", "joki", "батут"]):
            c_tag = "play"

        set_user_last_trip(message.from_user.id, raw_text, "kids")
        res = await plan_kid_entertainment(message.from_user.id, query=raw_text, age_group="1-3", category=c_tag)
        await render_kid_entertainment(message, res, category=c_tag)
        return

    # Обычный запрос загородного маршрута / уикенда
    set_user_last_trip(message.from_user.id, raw_text, "general")
    res = await plan_weekend_activity(message.from_user.id, raw_text, mode_type="general")
    await render_weekend_plan(message, res, mode_type="general")


async def render_kid_entertainment(message: types.Message, res: dict, category: str = "all"):
    title = html.escape(str(res.get("title", "Детское развлечение")))
    cat_name = html.escape(str(res.get("category_name", "Развлечение для малыша 1–3 года")))
    age_range = html.escape(str(res.get("age_range", "🎯 Строго 1–3 года (малыши и тоддлеры)")))
    addr = html.escape(str(res.get("address", "")))
    tickets = html.escape(str(res.get("tickets", "")))
    sched = html.escape(str(res.get("schedule", "")))
    high = html.escape(str(res.get("highlights", "")))
    comfort = html.escape(str(res.get("toddler_comfort", "")))
    food = html.escape(str(res.get("food_nearby", "")))
    logistics = html.escape(str(res.get("logistics", "")))
    tip = html.escape(str(res.get("tip_for_parents", "")))

    lines = [
        f"🎈 <b>{title.upper()}</b>\n",
        f"📌 Категория: <b>{cat_name}</b>",
        f"👶 Возраст: <b>{age_range}</b>\n",
        f"📍 <b>Адрес и метро:</b>\n<code>{addr}</code>\n",
        f"💵 <b>Цены на билеты:</b>\n{tickets}\n",
        f"⏰ <b>График работы:</b>\n{sched}\n",
        f"✨ <b>Что понравится малышу (1–3 года):</b>\n{high}\n"
    ]

    if comfort:
        lines.append(f"🍼 <b>Комфорт для малыша и мамы:</b>\n{comfort}\n")
    if food:
        lines.append(f"🥣 <b>Где покормить малыша (детское меню):</b>\n{food}\n")
    if logistics:
        lines.append(f"🚗 <b>Как добраться и с коляской:</b>\n{logistics}\n")
    if tip:
        lines.append(f"💡 <b>Совет родителям тоддлера:</b>\n<i>{tip}</i>\n")

    lines.append("<i>👇 Нажмите «🔄 Другой вариант для малыша (Ещё)», чтобы увидеть следующую локацию!</i>")

    await message.answer(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=get_kid_result_keyboard(category)
    )


async def render_weekend_plan(message: types.Message, res: dict, mode_type: str = "general"):
    title = html.escape(str(res.get("title", "Сценарий выходных")))
    vibe = html.escape(str(res.get("vibe_summary", "")))
    kids = html.escape(str(res.get("kid_friendly_rating", "")))
    food = html.escape(str(res.get("pit_stops_food", "")))
    road = html.escape(str(res.get("road_tips", "")))
    budget = html.escape(str(res.get("weather_budget_estimate", "")))
    locations = res.get("key_locations", [])

    lines = [
        f"🌲 <b>{title.upper()}</b>\n",
        f"🎯 <b>Вайб поездки:</b> <i>{vibe}</i>\n"
    ]

    if kids:
        lines.append(f"👶 <b>Для детей:</b>\n{kids}\n")

    lines.append("📍 <b>КЛЮЧЕВЫЕ ТОЧКИ МАРШРУТА:</b>")
    for idx, loc in enumerate(locations, 1):
        name = html.escape(str(loc.get("name", "Точка")))
        addr = html.escape(str(loc.get("address", "")))
        price = html.escape(str(loc.get("price", "")))
        high = html.escape(str(loc.get("highlight", "")))
        lines.append(
            f"<b>{idx}. {name}</b>\n"
            f"   🏠 Адрес: <code>{addr}</code>\n"
            f"   💵 Стоимость: {price}\n"
            f"   ✨ Фишка: <i>{high}</i>\n"
        )

    if food:
        lines.append(f"🍔 <b>Где вкусно перекусить по пути:</b>\n{food}\n")
    if road:
        lines.append(f"🚗 <b>Дорога, АЗС и парковка:</b>\n{road}\n")
    if budget:
        lines.append(f"💰 <b>Оценка бюджета и погода:</b>\n{budget}")

    lines.append("\n<i>💡 Нажмите «🔄 Другой маршрут (Ещё)» ниже, чтобы посмотреть следующий вариант!</i>")

    await message.answer(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=get_plan_result_keyboard(mode_type)
    )
