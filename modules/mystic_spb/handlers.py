"""
Обработчики модуля «Тайный Петербург» и интерактивных пеших экскурсий-квестов.
Позволяет пользователю выбрать или ввести начальную точку, получить 3 варианта
маршрута с культовыми заведениями и пошагово проходить экскурсию от точки к точке.
"""

import re
import html
import logging
from typing import Dict, Any, List, Optional
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.keyboards import get_main_menu, is_exit_command
from core.states import ActiveModeStates
from modules.voice_assistant.transcriber import transcribe_audio_gemini
from modules.mystic_spb.storyteller import get_mystic_spb_story
from modules.mystic_spb.tour_guide import generate_spb_tours, get_curated_tours_for_area
from modules.mystic_spb.session_manager import (
    start_tour_session,
    get_active_tour_session,
    advance_tour_session,
    cancel_tour_session,
    get_current_stop,
    get_next_stop
)
from modules.mystic_spb.keyboards import (
    get_spb_gps_mode_keyboard,
    get_mystic_keyboard,
    get_tour_start_keyboard,
    get_tour_selection_keyboard,
    get_tour_step_keyboard,
    get_tour_next_navigation_keyboard,
    get_tour_finish_keyboard
)

logger = logging.getLogger("MysticSPBHandlers")
router = Router(name="mystic_spb")

# Кэш сгенерированных вариантов туров для каждого пользователя
user_pending_tours: Dict[int, List[Dict[str, Any]]] = {}


# =====================================================================
# 1. ГЛАВНЫЙ ВХОД В МОДУЛЬ «ТАЙНЫЙ ПЕТЕРБУРГ»
# =====================================================================
@router.message(Command("spb_mystic"))
@router.message(Command("spb"))
@router.message(Command("tour"))
@router.message(Command("walk"))
@router.message(F.text.in_([
    "🕵️‍♂️ Тайный СПб", "Тайный СПб", "Мистический Петербург",
    "Мистический СПб", "Легенды СПб", "🚶‍♂️ Погулять по СПб (Экскурсия)",
    "Погулять по СПб", "Экскурсия", "Прогулка"
]))
async def cmd_mystic_spb(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.mystic_spb_mode)

    # Если нажата именно кнопка прогулки — сразу открываем меню экскурсий
    raw_text = (message.text or "").strip()
    if any(k in raw_text.lower() for k in ["погулять", "экскурсия", "прогулка", "tour", "walk"]):
        await show_tour_start_menu(message, state)
        return

    text = (
        "🕵️‍♂️ <b>Тайный, Исторический & Мистический Петербург:</b>\n\n"
        "Я ваш персональный сталкер и эксперт по <b>городским тайнам, расследованиям «ЗА и ПРОТИВ», "
        "бандитскому следу, культовым заведениям и интерактивным пешим экскурсиям!</b>\n\n"
        "🚶‍♂️ <b>ЧТО УМЕЕТ МОДУЛЬ:</b>\n"
        "1. 🧭 <b>Интерактивные экскурсии-квесты с ведением по шагам:</b>\n"
        "   Напишите <i>«Хочу погулять»</i> или стартовую точку (например, <i>«Погулять от Сенной»</i>, <i>«Экскурсия от Петроградки»</i>) — "
        "я предложу 3 разных маршрута, проведу от точки к точке, расскажу, что здесь было, и покажу культовые заведения по пути!\n\n"
        "2. 📍 <b>Тайны конкретного места:</b>\n"
        "   Нажмите кнопку геопозиции или напишите любое место (<i>«Англетер»</i>, <i>«Ротонда»</i>, <i>«Юсуповский дворец»</i>) — "
        "я раскрою историческое расследование и машину времени «Тогда vs Сейчас».\n\n"
        "👇 <b>Выберите действие или нажмите «Собрать маршрут для прогулки»:</b>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_spb_gps_mode_keyboard())
    await message.answer("👇 <b>Быстрый старт:</b>", parse_mode=ParseMode.HTML, reply_markup=get_mystic_keyboard())


# =====================================================================
# 2. МЕНЮ СТАРТА ЭКСКУРСИИ
# =====================================================================
async def show_tour_start_menu(target_msg: types.Message, state: FSMContext):
    """Показывает меню выбора начальной точки экскурсии."""
    await state.set_state(ActiveModeStates.mystic_spb_mode)
    text = (
        "🚶‍♂️ <b>Пешая экскурсия-квест по Санкт-Петербургу:</b>\n\n"
        "Я составлю для вас <b>небанальный авторский маршрут</b> с пошаговым сопровождением, "
        "городскими легендами и <b>культовыми заведениями по пути</b> (легендарные пышечные, старейшие рюмочные, "
        "секретные кофейни в арках и видовые бары).\n\n"
        "📍 <b>Откуда стартуем?</b>\n"
        "• Выберите популярный исторический район на кнопках ниже,\n"
        "• Отправьте свою текущую геопозицию 📍,\n"
        "• Или просто <b>напишите в чат любой адрес, станцию метро или памятник</b> (например: <i>«Чернышевская»</i>, <i>«Маяковская»</i>, <i>«Коломна»</i>, <i>«Адмиралтейство»</i>):"
    )
    await target_msg.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_tour_start_keyboard())


@router.callback_query(F.data == "spb_tour_menu")
async def cb_tour_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_tour_start_menu(callback.message, state)


@router.callback_query(F.data == "spb_back_to_mystic")
async def cb_back_to_mystic(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "👇 <b>Популярные мистические и детективные локации Санкт-Петербурга:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_mystic_keyboard()
    )


# =====================================================================
# 3. ВЫБОР НАЧАЛЬНОЙ ТОЧКИ И ГЕНЕРАЦИЯ 3 ВАРИАНТОВ МАРШРУТА
# =====================================================================
@router.callback_query(F.data.startswith("spb_tstart_"))
async def cb_tour_preset_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.mystic_spb_mode)
    key = callback.data.replace("spb_tstart_", "")

    if key == "gps":
        await callback.answer("Отправьте геопозицию через кнопку внизу!", show_alert=True)
        await callback.message.answer(
            "📍 <b>Нажмите кнопку «📍 Отправить мою геопозицию»</b> внизу экрана, чтобы я построил экскурсию прямо от места, где вы сейчас стоите!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_spb_gps_mode_keyboard()
        )
        return

    preset_map = {
        "nevsky": "Невский проспект и Гостиный Двор",
        "sennaya": "Сенная площадь и Коломна",
        "petrogradka": "Петроградская сторона и Горьковская",
        "vasilievsky": "Васильевский остров и Стрелка",
        "chernyshevskaya": "Чернышевская и Литейная часть"
    }
    start_point = preset_map.get(key, "Невский проспект")
    await callback.answer(f"Ищу маршруты от: {start_point[:25]}...")
    await process_and_show_tour_options(callback.message, callback.from_user.id, start_point, state)


async def process_and_show_tour_options(message: types.Message, user_id: int, start_point: str, state: FSMContext):
    """Генерирует и выводит 3 варианта пешей экскурсии."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    status_msg = await message.answer(
        f"🕵️‍♂️ <i>Сканирую городские архивы и тайные дворы от точки «{html.escape(start_point)}»...\nПодбираю 3 авторских маршрута с культовыми заведениями...</i>",
        parse_mode=ParseMode.HTML
    )

    tours = await generate_spb_tours(user_id, start_point)
    user_pending_tours[user_id] = tours
    await state.update_data(spb_pending_tours=tours, spb_tour_start_point=start_point)

    # Удаляем или обновляем статусное сообщение
    try:
        await status_msg.delete()
    except Exception:
        pass

    cards = [
        f"🚶‍♂️ <b>ГОТОВЫ 3 АВТОРСКИХ МАРШРУТА ОТ «{html.escape(start_point).upper()}»:</b>\n",
        "Выберите понравившуюся атмосферу — я поведу вас шаг за шагом с историческими рассказами и остановками в культовых заведениях!\n"
    ]

    icons = ["🕵️‍♂️", "🍸", "🏛"]
    for idx, t in enumerate(tours[:3]):
        icon = icons[idx % len(icons)]
        title = html.escape(str(t.get("title", f"Маршрут №{idx+1}")))
        theme = html.escape(str(t.get("theme", "")))
        dist = html.escape(str(t.get("total_distance", "~2.5 км")))
        dur = html.escape(str(t.get("duration", "1.5–2 часа")))
        stops_count = len(t.get("stops", []))
        venue = html.escape(str(t.get("highlight_venue", "Культовое заведение")))

        cards.append(
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{icon} <b>ВАРИАНТ {idx+1}: «{title}»</b>\n"
            f"🎭 <b>Вайб:</b> {theme}\n"
            f"⏱ <b>Маршрут:</b> {dist} • {dur} • {stops_count} ключевые точки\n"
            f"☕️ <b>По пути:</b> {venue}"
        )

    cards.append("\n👇 <b>Выберите вариант маршрута для старта экскурсии:</b>")
    full_text = "\n".join(cards)

    await message.answer(
        full_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_tour_selection_keyboard(tours)
    )


# =====================================================================
# 4. ВЫБОР МАРШРУТА И СТАРТ ПОШАГОВОГО КВЕСТА
# =====================================================================
@router.callback_query(F.data.startswith("spb_tsel_"))
async def cb_select_tour(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.set_state(ActiveModeStates.mystic_spb_mode)

    try:
        tour_idx = int(callback.data.replace("spb_tsel_", ""))
    except ValueError:
        tour_idx = 0

    tours = user_pending_tours.get(user_id)
    if not tours:
        data = await state.get_data()
        tours = data.get("spb_pending_tours", [])

    if not tours or tour_idx >= len(tours):
        await callback.answer("Маршруты устарели, давайте подберем заново!", show_alert=True)
        await show_tour_start_menu(callback.message, state)
        return

    selected_tour = tours[tour_idx]
    session = start_tour_session(user_id, selected_tour)
    await state.update_data(spb_active_tour_session=session)

    await callback.answer(f"Стартуем: {selected_tour.get('title', '')[:25]}!")
    await render_tour_step(callback.message, session, is_start=True)


async def render_tour_step(message: types.Message, session: Dict[str, Any], is_start: bool = False):
    """Рендерит карточку движения к текущей точке с навигацией и культовым заведением."""
    tour = session.get("tour", {})
    stops = tour.get("stops", [])
    idx = session.get("current_stop_idx", 0)

    if idx >= len(stops):
        await render_tour_finish(message, session)
        return

    stop = stops[idx]
    stop_name = html.escape(str(stop.get("name", f"Точка {idx+1}")))
    address = html.escape(str(stop.get("address", "")))
    how_to_reach = html.escape(str(stop.get("how_to_reach", "")))
    maps_url = stop.get("maps_url", "")

    header = "🚀 <b>ЭКСКУРСИЯ НАЧАЛАСЬ!</b>\n" if is_start else ""
    tour_title = html.escape(str(tour.get("title", "Экскурсия по СПб")))

    lines = [
        f"{header}🧭 <b>Маршрут: «{tour_title}»</b>\n",
        f"🚩 <b>ТОЧКА {idx+1} ИЗ {len(stops)}: {stop_name.upper()}</b>",
        f"📍 <b>Адрес:</b> {address}\n",
        f"🧭 <b>КАК ДОЙТИ:</b>\n{how_to_reach}\n"
    ]

    spot = stop.get("spot_by_the_way")
    if spot:
        spot_name = html.escape(str(spot.get("name", "")))
        spot_type = html.escape(str(spot.get("type", "Культовое место")))
        spot_recom = html.escape(str(spot.get("recommendation", "")))
        lines.append(
            "━━━━━━━━━━━━━━━━━━━\n"
            f"☕️ <b>КУЛЬТОВОЕ ЗАВЕДЕНИЕ ПО ПУТИ:</b>\n"
            f"🔹 <b>{spot_name}</b> ({spot_type})\n"
            f"👉 <i>{spot_recom}</i>\n"
        )

    lines.append(
        "━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Когда дойдете до места — нажмите кнопку ниже или напишите «я на месте» (можно надиктовать голосом 🎙) — я расскажу всё, что здесь происходило!</i>"
    )

    await message.answer(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=get_tour_step_keyboard(session)
    )


# =====================================================================
# 5. ПОЛЬЗОВАТЕЛЬ ПРИШЕЛ НА ТОЧКУ («Я НА МЕСТЕ»)
# =====================================================================
@router.callback_query(F.data.startswith("spb_tarrived_"))
async def cb_tour_arrived(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = get_active_tour_session(user_id)
    if not session:
        await callback.answer("Нет активной экскурсии. Давайте начнем новую!", show_alert=True)
        await show_tour_start_menu(callback.message, state)
        return

    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("Рассказываю тайны этого места...")
    await handle_arrival_at_stop(callback.message, user_id, session, state)


async def handle_arrival_at_stop(message: types.Message, user_id: int, session: Dict[str, Any], state: FSMContext):
    """Выдает глубокий рассказ о точке и навигацию к следующему шагу."""
    tour = session.get("tour", {})
    stops = tour.get("stops", [])
    idx = session.get("current_stop_idx", 0)

    if idx >= len(stops):
        await render_tour_finish(message, session)
        return

    stop = stops[idx]
    stop_name = html.escape(str(stop.get("name", f"Точка {idx+1}")))
    address = html.escape(str(stop.get("address", "")))
    story = html.escape(str(stop.get("story", "")))
    look_for = html.escape(str(stop.get("look_for", "")))
    then_vs_now = html.escape(str(stop.get("then_vs_now", "")))

    has_next = (idx + 1 < len(stops))

    lines = [
        f"🏛 <b>ВЫ У ТОЧКИ {idx+1}: {stop_name.upper()}</b>\n",
        f"📜 <b>ЧТО ЗДЕСЬ БЫЛО:</b>\n{story}\n",
        "━━━━━━━━━━━━━━━━━━━",
        f"👁 <b>ПОСМОТРИТЕ ПРЯМО СЕЙЧАС (Секретная деталь):</b>\n👉 <i>{look_for}</i>\n"
    ]

    if then_vs_now:
        lines.append(
            f"📸 <b>ВИЗУАЛЬНО «ТОГДА И СЕЙЧАС»:</b>\n<i>{then_vs_now}</i>\n"
        )

    if has_next:
        next_stop = stops[idx + 1]
        next_name = html.escape(str(next_stop.get("name", "")))
        next_dir = html.escape(str(stop.get("next_direction", f"Идем к точке: {next_name}")))
        lines.append(
            "━━━━━━━━━━━━━━━━━━━\n"
            f"🚶‍♂️ <b>КУДА ИДЕМ ДАЛЬШЕ (ТОЧКА {idx+2}):</b>\n"
            f"👉 <b>{next_name}</b>\n"
            f"🧭 {next_dir}\n"
        )
    else:
        lines.append(
            "━━━━━━━━━━━━━━━━━━━\n"
            "🏆 <b>Это была финальная точка нашего маршрута!</b>\n"
            "Нажмите кнопку ниже, чтобы подвести итоги прогулки и узнать, где приятно завершить вечер!"
        )

    await message.answer(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=get_tour_next_navigation_keyboard(session, has_next=has_next)
    )


# =====================================================================
# 6. ПЕРЕХОД К СЛЕДУЮЩЕЙ ТОЧКЕ МАРШРУТА
# =====================================================================
@router.callback_query(F.data.startswith("spb_tnext_"))
async def cb_tour_next(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = advance_tour_session(user_id)
    if not session:
        await callback.answer("Экскурсия завершена или не найдена.", show_alert=True)
        await show_tour_start_menu(callback.message, state)
        return

    await callback.answer("Идем к следующей точке!")
    await render_tour_step(callback.message, session, is_start=False)


# =====================================================================
# 7. ПРОПУСК ТОЧКИ И ПОДРОБНОСТИ О ЗАВЕДЕНИИ
# =====================================================================
@router.callback_query(F.data.startswith("spb_tskip_"))
async def cb_tour_skip(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = advance_tour_session(user_id)
    if not session or session.get("status") == "finished":
        await callback.answer("Точки маршрута пройдены!")
        if session:
            await render_tour_finish(callback.message, session)
        return

    await callback.answer("Точка пропущена, переходим к следующей!")
    await render_tour_step(callback.message, session, is_start=False)


@router.callback_query(F.data.startswith("spb_tvenue_"))
async def cb_tour_venue_info(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = get_active_tour_session(user_id)
    if not session:
        await callback.answer("Экскурсия не найдена", show_alert=True)
        return

    try:
        stop_idx = int(callback.data.replace("spb_tvenue_", ""))
    except ValueError:
        stop_idx = session.get("current_stop_idx", 0)

    stops = session.get("tour", {}).get("stops", [])
    if stop_idx >= len(stops):
        await callback.answer("Заведение не найдено", show_alert=True)
        return

    stop = stops[stop_idx]
    spot = stop.get("spot_by_the_way")
    if not spot:
        await callback.answer("Рядом с этой точкой заведение не указано", show_alert=True)
        return

    await callback.answer()
    spot_name = html.escape(str(spot.get("name", "")))
    spot_addr = html.escape(str(spot.get("address", "")))
    spot_type = html.escape(str(spot.get("type", "Культовое место")))
    spot_recom = html.escape(str(spot.get("recommendation", "")))
    maps_url = spot.get("maps_url", "")

    text = (
        f"☕️ <b>КУЛЬТОВОЕ ЗАВЕДЕНИЕ ПО ПУТИ:</b>\n\n"
        f"🏛 <b>{spot_name}</b>\n"
        f"📌 <b>Формат:</b> {spot_type}\n"
        f"📍 <b>Адрес:</b> {spot_addr}\n\n"
        f"🍽 <b>ЧТО ПОПРОБОВАТЬ / ФИШКА:</b>\n"
        f"{spot_recom}\n\n"
        f"💡 <i>Отличное место, чтобы взять согревающий напиток с собой или сделать атмосферную паузу на 15 минут!</i>"
    )

    kb = []
    if maps_url:
        kb.append([InlineKeyboardButton(text="🗺 Открыть заведение на Яндекс.Картах ↗", url=maps_url)])
    kb.append([InlineKeyboardButton(text="🔙 Вернуться к маршруту", callback_data=f"spb_tback_step_{stop_idx}")])

    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data.startswith("spb_tback_step_"))
async def cb_back_to_step(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = get_active_tour_session(user_id)
    if session:
        await callback.answer()
        await render_tour_step(callback.message, session, is_start=False)
    else:
        await callback.answer("Экскурсия завершена")


# =====================================================================
# 8. ФИНИШ И ОТМЕНА ЭКСКУРСИИ
# =====================================================================
@router.callback_query(F.data == "spb_tfinish")
async def cb_tour_finish(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session = advance_tour_session(user_id)
    await callback.answer("Поздравляем с прохождением!")
    await render_tour_finish(callback.message, session or {})


async def render_tour_finish(message: types.Message, session: Dict[str, Any]):
    """Рендерит поздравление с завершением экскурсии и рекомендацию бара/ресторана для финала."""
    tour = session.get("tour", {})
    title = html.escape(str(tour.get("title", "Экскурсия по Санкт-Петербургу")))
    stops = tour.get("stops", [])
    dist = html.escape(str(tour.get("total_distance", "~2.5 км")))

    text = (
        f"🏆 <b>ЭКСКУРСИЯ УСПЕШНО ЗАВЕРШЕНА!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Вы полностью прошли авторский маршрут <b>«{title}»</b>!\n\n"
        f"📊 <b>ИТОГИ ПРОГУЛКИ:</b>\n"
        f"• Пройдено пешком: <b>{dist}</b>\n"
        f"• Исследовано ключевых локаций: <b>{len(stops)}</b>\n"
        f"• Раскрыты тайны старого города, найдены скрытые дворы и секретные детали фасадов!\n\n"
        f"🍸 <b>ГДЕ ОТМЕТИТЬ И ЗАВЕРШИТЬ ВЕЧЕР:</b>\n"
        f"Загляните в ближайший атмосферный бар или ресторан неподалеку — выпейте бокал авторского коктейля, "
        f"чашку кофе или фирменную настойку, чтобы обсудить увиденное!\n\n"
        f"👇 <b>Куда отправимся дальше?</b>"
    )

    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_tour_finish_keyboard()
    )


@router.callback_query(F.data == "spb_tcancel")
async def cb_tour_cancel(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cancel_tour_session(user_id)
    await callback.answer("Экскурсия завершена")
    await callback.message.answer(
        "🏁 <b>Пешая экскурсия завершена.</b>\nВы можете выбрать другой маршрут или исследовать отдельные городские тайны:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_mystic_keyboard()
    )


# =====================================================================
# 9. КНОПКИ ПРЕСЕТОВ ОТДЕЛЬНЫХ МИСТИЧЕСКИХ ЛОКАЦИЙ
# =====================================================================
@router.callback_query(F.data.startswith("mspb_loc_"))
async def cb_mystic_preset(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.mystic_spb_mode)
    loc_key = callback.data.replace("mspb_loc_", "")
    preset_names = {
        "angleterre": "Гостиница Англетер, Исаакиевская площадь (Тайна гибели Сергея Есенина)",
        "manezhnaya": "Манежная площадь и Итальянская улица, Санкт-Петербург",
        "yusupov": "Юсуповский дворец на Мойке (Убийство Григория Распутина)",
        "castle": "Михайловский (Инженерный) замок (Заговор и призрак Павла I)",
        "pushkin": "Место дуэли Пушкина на Черной речке и Комендантская дача",
        "random": "Секретный мистический двор и криминальная легенда центра Санкт-Петербурга"
    }
    query = preset_names.get(loc_key, "Тайны Санкт-Петербурга")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer(f"Исследую {query[:30]}...")
    res = await get_mystic_spb_story(callback.from_user.id, query)
    await render_mystic_story(callback.message, res)


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_mystic(callback: types.CallbackQuery, state: FSMContext):
    """Выход из режима «Тайный Петербург» в главное меню."""
    await state.clear()
    await callback.answer("Вы вышли в главное меню")
    await callback.message.answer(
        "🏁 <b>Режим «Тайный Петербург» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


# =====================================================================
# 10. ОБРАБОТКА ГЕОЛОКАЦИИ (GPS)
# =====================================================================
@router.message(ActiveModeStates.mystic_spb_mode, F.location)
async def handle_spb_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = message.from_user.id

    # Проверяем, идет ли активная экскурсия
    session = get_active_tour_session(user_id)
    if session:
        await message.answer("📍 <b>Геопозиция получена!</b> Вы находитесь у точки маршрута.")
        await handle_arrival_at_stop(message, user_id, session, state)
        return

    # Если экскурсия не идет — предлагаем либо отдельную историю, либо построить тур отсюда
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await get_mystic_spb_story(user_id, f"Геолокация ({lat}, {lon})", lat=lat, lon=lon)
    await render_mystic_story(message, res)

    # Кнопка начать экскурсию от текущих координат
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚶‍♂️ Начать пешую экскурсию отсюда", callback_data=f"spb_tstart_gps_coords")]
    ])
    await message.answer("💡 <b>Хотите пойти на полноценную экскурсию от этой точки?</b>", reply_markup=kb)


# =====================================================================
# 11. ГОЛОСОВЫЕ СООБЩЕНИЯ В РЕЖИМЕ ЭКСКУРСИИ
# =====================================================================
@router.message(ActiveModeStates.mystic_spb_mode, F.voice | F.video_note | F.audio)
async def handle_spb_voice(message: types.Message, state: FSMContext):
    """Распознает голос через Gemini Multimodal и передает в текстовый обработчик."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    file_id = None
    if message.voice:
        file_id = message.voice.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    elif message.audio:
        file_id = message.audio.file_id

    if not file_id:
        return

    file_obj = await message.bot.get_file(file_id)
    file_bytes_io = await message.bot.download_file(file_obj.file_path)
    audio_bytes = file_bytes_io.getvalue()

    recognized_text = await transcribe_audio_gemini(audio_bytes)
    if not recognized_text:
        await message.answer("🎙 <i>Не удалось разобрать голос, напишите текстом!</i>", parse_mode=ParseMode.HTML)
        return

    await message.answer(f"🗣 <i>Вы сказали: «{html.escape(recognized_text)}»</i>", parse_mode=ParseMode.HTML)

    # Создаем фиктивный текстовый запрос
    message.text = recognized_text
    await handle_spb_text(message, state)


# =====================================================================
# 12. ТЕКСТОВЫЕ СООБЩЕНИЯ И ДИАЛОГ
# =====================================================================
@router.message(ActiveModeStates.mystic_spb_mode, F.text)
async def handle_spb_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    user_id = message.from_user.id

    if is_exit_command(raw_text):
        await state.clear()
        cancel_tour_session(user_id)
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Тайный Петербург» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    text_lower = raw_text.lower()

    # 1. Проверяем, есть ли активная экскурсия и подтверждает ли пользователь прибытие
    session = get_active_tour_session(user_id)
    arrival_keywords = ["я на месте", "на месте", "дошел", "дошёл", "пришел", "пришёл", "что тут", "что здесь", "расскажи", "рассказывай", "дальше"]
    if session and any(k in text_lower for k in arrival_keywords):
        await handle_arrival_at_stop(message, user_id, session, state)
        return

    # 2. Проверяем запрос на прогулку / экскурсию («хочу погулять», «экскурсия от...», «маршрут»)
    walk_keywords = ["погулять", "прогулк", "экскурси", "маршрут", "поход по городу", "пройтись", "куда сходить"]
    if any(k in text_lower for k in walk_keywords):
        # Проверяем, указана ли начальная точка прямо в запросе
        # Например: «хочу погулять от сенной», «экскурсия по петроградке», «маршрут от чернышевской»
        cleaned_start = re_extract_start_point(raw_text)
        if cleaned_start:
            await process_and_show_tour_options(message, user_id, cleaned_start, state)
        else:
            await show_tour_start_menu(message, state)
        return

    # 3. Если пользователь просто ввел название места / улицы (например, «Сенная», «Невский 25», «Литейный», «Манежная»)
    # Проверяем: если это похоже на начальную точку для тура (или пользователь выбирает старт)
    # Если введено короткое название локации / улицы
    if len(raw_text) <= 40 and not any(q in text_lower for q in ["почему", "зачем", "кто такой", "когда"]):
        # Предлагаем варианты экскурсии от этой точки
        await process_and_show_tour_options(message, user_id, raw_text, state)
        return

    # 4. Общий поиск историко-мистической карточки места через storyteller
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await get_mystic_spb_story(user_id, raw_text)
    await render_mystic_story(message, res)


def re_extract_start_point(text: str) -> Optional[str]:
    """Извлекает начальную точку из фразы вида 'хочу погулять от Сенной' или 'экскурсия по Петроградке'."""
    patterns = [
        r"(?:погулять|прогулка|экскурсия|маршрут)\s+(?:от|начиная с|с|по|вокруг)\s+(.+)",
        r"(?:от|с)\s+([А-Яа-я0-9\s\-]+?)\s+(?:погулять|экскурси|маршрут)"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            extracted = m.group(1).strip()
            # Очищаем от лишних знаков препинания
            extracted = re.sub(r"^[,\.\s]+|[,\.\s]+$", "", extracted)
            if len(extracted) >= 3:
                return extracted
    return None


async def render_mystic_story(message: types.Message, res: dict):
    """Выводит подробную детективно-мистическую карточку локации."""
    loc_name = html.escape(str(res.get("location_name", "Санкт-Петербург")))
    origin = html.escape(str(res.get("name_origin", "")))
    chronicle = html.escape(str(res.get("era_chronicle", "")))
    invest = res.get("historical_investigation", {})
    inv_title = html.escape(str(invest.get("title", "Историческое расследование")))
    facts_pro = html.escape(str(invest.get("facts_pro", "")))
    facts_contra = html.escape(str(invest.get("facts_contra", "")))
    crime = html.escape(str(res.get("crime_and_legends", "")))
    then_now = html.escape(str(res.get("then_and_now_visual", "")))
    secret = html.escape(str(res.get("secret_doorway", "")))
    route = html.escape(str(res.get("next_quest_route", "")))

    lines = [
        f"🏛 <b>{loc_name.upper()}</b>\n",
        f"📍 <b>Откуда пошло название:</b>\n<i>{origin}</i>\n",
        f"📜 <b>Хроника сквозь эпохи:</b>\n{chronicle}\n",
        "━━━━━━━━━━━━━━━━━━━",
        f"⚖️ <b>РАССЛЕДОВАНИЕ: «{inv_title}»</b>",
        f"🟢 <b>Версия ЗА:</b> {facts_pro}",
        f"🔴 <b>Факты ПРОТИВ / Тайная версия:</b> {facts_contra}\n",
        "━━━━━━━━━━━━━━━━━━━",
        f"💀 <b>Криминальный след & Мистика:</b>\n{crime}\n",
        f"📸 <b>ВИЗУАЛЬНО «ТОГДА И СЕЙЧАС» (Машина времени):</b>\n<i>{then_now}</i>\n",
        f"👁 <b>Секретная пасхалка рядом:</b>\n👉 {secret}\n",
        f"🚶‍♂️ <b>Пеший маршрут-квест дальше:</b>\n{route}"
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚶‍♂️ Начать пешую экскурсию отсюда", callback_data="spb_tour_menu")],
        [InlineKeyboardButton(text="🎲 Другая тайна СПб", callback_data="mspb_loc_random")],
        [InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")]
    ])

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
