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
                InlineKeyboardButton(text="👶 Куда с ребенком (по возрасту)", callback_data="wt_kids_menu"),
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
    """Интерактивное меню выбора детских развлечений по возрасту и категориям."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👶 1–3 года (Малыши)", callback_data="wt_kid_age_1-3"),
                InlineKeyboardButton(text="🧒 4–6 лет (Дошкольники)", callback_data="wt_kid_age_4-6")
            ],
            [
                InlineKeyboardButton(text="👦 7–10 лет (Школьники)", callback_data="wt_kid_age_7-10"),
                InlineKeyboardButton(text="🧑 11–14+ лет (Подростки)", callback_data="wt_kid_age_11-14")
            ],
            [
                InlineKeyboardButton(text="🐠 Океанариум & Зоопарки", callback_data="wt_kid_cat_zoo"),
                InlineKeyboardButton(text="🌊 Аквапарки & Бассейны", callback_data="wt_kid_cat_aqua")
            ],
            [
                InlineKeyboardButton(text="🏰 Игровые парки (Joki, КидБург)", callback_data="wt_kid_cat_play"),
                InlineKeyboardButton(text="🔬 Наука & Музеи (Гранд Макет)", callback_data="wt_kid_cat_science")
            ],
            [
                InlineKeyboardButton(text="🎲 Топ детское место сейчас", callback_data="wt_kid_random")
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
                InlineKeyboardButton(text="👶 Развлечения с детьми", callback_data="wt_kids_menu"),
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


def get_kid_result_keyboard(age_group: str = "all", category: str = "all") -> InlineKeyboardMarkup:
    """Клавиатура под карточкой детского развлечения."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другое развлечение (Ещё)", callback_data=f"wt_kid_more_{age_group}_{category}")
            ],
            [
                InlineKeyboardButton(text="👶 1–3 г", callback_data="wt_kid_age_1-3"),
                InlineKeyboardButton(text="🧒 4–6 лет", callback_data="wt_kid_age_4-6"),
                InlineKeyboardButton(text="👦 7–10 л", callback_data="wt_kid_age_7-10"),
                InlineKeyboardButton(text="🧑 11–14+", callback_data="wt_kid_age_11-14")
            ],
            [
                InlineKeyboardButton(text="🐠 Зоопарки", callback_data="wt_kid_cat_zoo"),
                InlineKeyboardButton(text="🌊 Аквапарки", callback_data="wt_kid_cat_aqua"),
                InlineKeyboardButton(text="🏰 Игровые", callback_data="wt_kid_cat_play"),
                InlineKeyboardButton(text="🔬 Музеи", callback_data="wt_kid_cat_science")
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
        "🌲 <b>Сценарист выходных, Отдых с детьми & Авто-Роадтрипы:</b>\n\n"
        "Я составляю готовые сценарии отдыха под ключ с маршрутами, ценами, АЗС и детской инфраструктурой!\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Куда поехать с сыном 5 лет на полдня?»</i>\n"
        "• <i>«Аквапарк или зоопарк в СПб для ребенка 4 года»</i>\n"
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

    # 2. Детское меню выбора возраста и категорий
    if cat in ["kids", "kids_menu"]:
        await callback.answer()
        text = (
            "👶 <b>Развлечения с детьми в Санкт-Петербурге и Ленобласти:</b>\n\n"
            "Зоопарки, океанариум, аквапарки, игровые парки (Joki Joya, КидБург, MazaPark), "
            "интерактивные научные музеи (Гранд Макет, ЛабиринтУм) и цирк под ключ!\n\n"
            "👇 <b>Выберите возраст ребенка или категорию:</b>"
        )
        await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_kids_menu_keyboard())
        return

    # 3. Подбор детского развлечения по возрасту
    if cat.startswith("kid_age_"):
        age_grp = cat.replace("kid_age_", "")
        await callback.answer(f"👶 Подбираю развлечения для {age_grp} лет...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        set_user_last_trip(callback.from_user.id, f"Детские развлечения для возраста {age_grp}", "kids")
        res = await plan_kid_entertainment(callback.from_user.id, age_group=age_grp, category="all")
        await render_kid_entertainment(callback.message, res, age_group=age_grp, category="all")
        return

    # 4. Подбор детского развлечения по категории (zoo, aqua, play, science)
    if cat.startswith("kid_cat_"):
        c_tag = cat.replace("kid_cat_", "")
        cat_names = {"zoo": "зоопарк / океанариум", "aqua": "аквапарк", "play": "игровой парк", "science": "интерактивный музей"}
        await callback.answer(f"🔎 Ищу {cat_names.get(c_tag, 'развлечение')}...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        set_user_last_trip(callback.from_user.id, f"Детские развлечения категории {c_tag}", "kids")
        res = await plan_kid_entertainment(callback.from_user.id, age_group="all", category=c_tag)
        await render_kid_entertainment(callback.message, res, age_group="all", category=c_tag)
        return

    # 5. Случайное детское место
    if cat == "kid_random":
        await callback.answer("🎲 Подбираю топ детское место...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        set_user_last_trip(callback.from_user.id, "Лучшее детское место в СПб", "kids")
        res = await plan_kid_entertainment(callback.from_user.id, age_group="all", category="all", is_another=True)
        await render_kid_entertainment(callback.message, res, age_group="all", category="all")
        return

    # 6. Кнопка «Другое детское развлечение (Ещё)»
    if cat.startswith("kid_more_"):
        parts = cat.replace("kid_more_", "").split("_")
        age_grp = parts[0] if len(parts) > 0 else "all"
        c_tag = parts[1] if len(parts) > 1 else "all"
        await callback.answer("🔄 Подбираю другое детское место...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        res = await plan_kid_entertainment(callback.from_user.id, age_group=age_grp, category=c_tag, is_another=True)
        await render_kid_entertainment(callback.message, res, age_group=age_grp, category=c_tag)
        return

    # 7. Другой загородный маршрут (для взрослых / роадтрипов)
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
            res = await plan_kid_entertainment(message.from_user.id, query="Другое детское развлечение", is_another=True)
            await render_kid_entertainment(message, res)
        else:
            query = last_info.get("query") or "Другой интересный сценарий проведения выходного дня"
            res = await plan_weekend_activity(message.from_user.id, query, mode_type=last_mode, is_another=True)
            await render_weekend_plan(message, res, mode_type=last_mode)
        return

    # Проверяем, относится ли запрос к детям / аквапаркам / зоопаркам
    kid_keywords = [
        "ребенок", "дети", "дочь", "сын", "детск", "детям", "малыш",
        "зоопарк", "аквапарк", "океанариум", "игровая комната", "joki",
        "джоки", "кидбург", "мазапарк", "батут", "скалодром", "цирк",
        "аттракцион", "альпак", "зубр", "тесла", "лабиринтум"
    ]

    is_kid_query = any(k in lower_text for k in kid_keywords)

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    if is_kid_query:
        # Определяем возраст
        age_grp = "all"
        if any(w in lower_text for w in ["1 год", "2 года", "3 года", "малыш", "1-3"]):
            age_grp = "1-3"
        elif any(w in lower_text for w in ["4 года", "5 лет", "6 лет", "дошкольн", "4-6"]):
            age_grp = "4-6"
        elif any(w in lower_text for w in ["7 лет", "8 лет", "9 лет", "10 лет", "школьн", "7-10"]):
            age_grp = "7-10"
        elif any(w in lower_text for w in ["11 лет", "12 лет", "13 лет", "14 лет", "подрост", "11-14"]):
            age_grp = "11-14"

        # Определяем категорию
        c_tag = "all"
        if any(w in lower_text for w in ["зоопарк", "океанариум", "животн", "альпак", "зубр", "рыб"]):
            c_tag = "zoo"
        elif any(w in lower_text for w in ["аквапарк", "бассейн", "водн"]):
            c_tag = "aqua"
        elif any(w in lower_text for w in ["игров", "комнат", "лабиринт", "батут", "joki", "джоки", "кидбург", "мазапарк"]):
            c_tag = "play"
        elif any(w in lower_text for w in ["музей", "наук", "макет", "тесла", "маги", "планетари"]):
            c_tag = "science"

        set_user_last_trip(message.from_user.id, raw_text, "kids")
        res = await plan_kid_entertainment(message.from_user.id, query=raw_text, age_group=age_grp, category=c_tag)
        await render_kid_entertainment(message, res, age_group=age_grp, category=c_tag)
        return

    # Обычный запрос загородного маршрута / уикенда
    set_user_last_trip(message.from_user.id, raw_text, "general")
    res = await plan_weekend_activity(message.from_user.id, raw_text, mode_type="general")
    await render_weekend_plan(message, res, mode_type="general")


async def render_kid_entertainment(message: types.Message, res: dict, age_group: str = "all", category: str = "all"):
    title = html.escape(str(res.get("title", "Детское развлечение")))
    cat_name = html.escape(str(res.get("category_name", "Развлечение для всей семьи")))
    age_range = html.escape(str(res.get("age_range", "Для детей")))
    addr = html.escape(str(res.get("address", "")))
    tickets = html.escape(str(res.get("tickets", "")))
    sched = html.escape(str(res.get("schedule", "")))
    high = html.escape(str(res.get("highlights", "")))
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
        f"✨ <b>Что больше всего понравится ребенку:</b>\n{high}\n"
    ]

    if food:
        lines.append(f"🍕 <b>Где поесть рядом (детское меню):</b>\n{food}\n")
    if logistics:
        lines.append(f"🚗 <b>Как добраться и парковка:</b>\n{logistics}\n")
    if tip:
        lines.append(f"💡 <b>Совет родителям:</b>\n<i>{tip}</i>\n")

    lines.append("<i>👇 Нажмите «🔄 Другое развлечение (Ещё)», чтобы увидеть следующую локацию!</i>")

    await message.answer(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=get_kid_result_keyboard(age_group, category)
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
