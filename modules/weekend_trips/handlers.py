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
from modules.weekend_trips.storage import get_user_last_trip, set_user_last_trip

logger = logging.getLogger("WeekendTripsHandlers")
router = Router(name="weekend_trips")


def get_weekend_keyboard() -> InlineKeyboardMarkup:
    """Стартовая клавиатура сценариев выходных."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👶 Куда с ребенком (по возрасту)", callback_data="wt_kids"),
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


def get_plan_result_keyboard(mode_type: str = "general") -> InlineKeyboardMarkup:
    """Клавиатура под готовым маршрутом: кнопка «Другой маршрут» на первом месте."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другой маршрут (Ещё)", callback_data=f"wt_another_{mode_type}")
            ],
            [
                InlineKeyboardButton(text="👶 С ребенком", callback_data="wt_kids"),
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
        "• <i>«С детьми 3 и 9 лет на природу с кафе и площадкой»</i>\n"
        "• <i>«Маршрут на машине в Карелию на 2 дня с красивыми видами»</i>\n"
        "• <i>«Что интересного проходит в эти выходные в СПб?»</i>\n\n"
        "💬 <i>Напишите ваш запрос или выберите кнопку:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Выходные"))
    await message.answer("👇 <b>Быстрый выбор сценария:</b>", reply_markup=get_weekend_keyboard())


@router.callback_query(F.data.startswith("wt_"))
async def cb_weekend_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.replace("wt_", "")
    await state.set_state(ActiveModeStates.weekend_planner_mode)

    if cat.startswith("another"):
        await callback.answer("🔄 Подбираю новый маршрут...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        m_type = cat.replace("another_", "").replace("another", "").strip("_") or "general"
        last_info = get_user_last_trip(callback.from_user.id)
        query = last_info.get("query") or "Другой отличный сценарий проведения выходного дня"
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type=m_type, is_another=True)
        await render_weekend_plan(callback.message, res, mode_type=m_type)
    elif cat == "kids":
        await callback.answer()
        await callback.message.answer(
            "💬 <b>Напишите возраст ребенка и пожелания:</b>\n"
            "<i>(Например: «С ребенком 4 года, любим животных и детские площадки на природе»)</i>",
            parse_mode=ParseMode.HTML
        )
    elif cat == "roadtrip":
        await callback.answer("🚗 Составляю авто-маршрут...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        query = "Топ авто-роадтрип из СПб на 1-2 дня: Карелия, Ладога или живописные окрестности с лучшими смотровыми и кафе"
        set_user_last_trip(callback.from_user.id, query, "roadtrip")
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type="roadtrip", is_another=True)
        await render_weekend_plan(callback.message, res, mode_type="roadtrip")
    elif cat == "afisha":
        await callback.answer("🎪 Ищу афишу и события...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        query = "Актуальная афиша событий в СПб на ближайшие выходные: фестивали, выставки, маркеты, мероприятия на крышах"
        set_user_last_trip(callback.from_user.id, query, "afisha")
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type="afisha", is_another=True)
        await render_weekend_plan(callback.message, res, mode_type="afisha")
    elif cat == "random":
        await callback.answer("🎲 Генерирую идеальный выходной...")
        await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
        query = "Лучший сценарий проведения выходного дня под текущий сезон"
        set_user_last_trip(callback.from_user.id, query, "general")
        res = await plan_weekend_activity(callback.from_user.id, query, mode_type="general", is_another=True)
        await render_weekend_plan(callback.message, res, mode_type="general")
    else:
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
        "давай другой", "не то", "следующий", "дальше", "поменяй"
    ]

    if lower_text in another_triggers:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        last_info = get_user_last_trip(message.from_user.id)
        m_type = last_info.get("mode", "general")
        query = last_info.get("query") or "Другой интересный сценарий проведения выходного дня"
        res = await plan_weekend_activity(message.from_user.id, query, mode_type=m_type, is_another=True)
        await render_weekend_plan(message, res, mode_type=m_type)
        return

    # Пользовательский текстовый запрос
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    mode_type = "kids" if any(w in lower_text for w in ["ребенок", "дети", "дочь", "сын", "детск", "лет"]) else "general"
    set_user_last_trip(message.from_user.id, raw_text, mode_type)
    res = await plan_weekend_activity(message.from_user.id, raw_text, mode_type=mode_type)
    await render_weekend_plan(message, res, mode_type=mode_type)


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
