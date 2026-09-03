import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from core.keyboards import get_main_menu
from core.states import ActiveModeStates
from modules.weather_synoptic.storage import (
    get_user_weather_config,
    set_user_weather_config
)
from modules.weather_synoptic.service import (
    geocode_location,
    reverse_geocode_location,
    get_weather_report
)

logger = logging.getLogger("WeatherHandlers")
router = Router(name="weather_synoptic")


def get_weather_keyboard(alerts_enabled: bool = True) -> InlineKeyboardMarkup:
    alert_btn_text = "🔔 Алерты дождя: ВКЛ" if alerts_enabled else "🔕 Алерты дождя: ВЫКЛ"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="w_refresh"),
                InlineKeyboardButton(text=alert_btn_text, callback_data="w_toggle_alert")
            ],
            [
                InlineKeyboardButton(text="🏙 Сменить район / город", callback_data="w_city_help")
            ]
        ]
    )


@router.message(Command("weather"))
@router.message(F.text.in_(["🌤 Погода", "🌤 Погода & Осадки", "Погода", "Погода & Осадки"]))
async def cmd_weather(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    raw_text = (message.text or "").strip()
    custom_query = ""

    # Only parse custom query if user sent explicit command /weather <city>
    if raw_text.startswith("/weather"):
        parts = raw_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            custom_query = parts[1].strip()

    config = get_user_weather_config(user_id)
    city = config.get("city", "Санкт-Петербург")
    district = config.get("district", "")
    lat = config.get("lat", 59.9386)
    lon = config.get("lon", 30.3141)

    if custom_query:
        geo = await geocode_location(custom_query)
        if geo:
            city, district, lat, lon = geo
        else:
            await message.answer(f"⚠️ Локация «{custom_query}» не найдена. Показываю погоду для {city}.")

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    success, report = await get_weather_report(city, district, lat, lon)

    if success:
        alerts_on = config.get("alerts_enabled", True)
        await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=get_weather_keyboard(alerts_on))
    else:
        await message.answer(f"❌ {report}")


@router.message(Command("set_city"))
@router.message(Command("set_district"))
async def cmd_set_city(message: types.Message):
    user_id = message.from_user.id
    args = (message.text or "").split(maxsplit=1)

    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "🏙 <b>Укажите ваш город и район:</b>\n\n"
            "<i>Примеры:</i>\n"
            "• <code>/set_city Санкт-Петербург, Приморский район</code>\n"
            "• <code>/set_city СПб, Васильевский остров</code>\n"
            "• <code>/set_city Москва, Хамовники</code>\n"
            "• <code>/set_city Сочи, Адлер</code>\n\n"
            "📍 <b>Или просто отправьте геометку (локацию)</b> с телефона через значок 📎 Скрепки!",
            parse_mode=ParseMode.HTML
        )
        return

    query = args[1].strip()
    geo = await geocode_location(query)
    if not geo:
        await message.answer(f"❌ Не удалось найти «{query}». Попробуйте написать точнее: <code>Город, Район</code>.", parse_mode=ParseMode.HTML)
        return

    city, district, lat, lon = geo
    set_user_weather_config(user_id, city=city, district=district, lat=lat, lon=lon, alerts_enabled=True)

    loc_str = f"<b>{city}</b>" + (f" (район <b>{district}</b>)" if district else "")

    await message.answer(
        f"✅ <b>Локация успешно обновлена: {loc_str}!</b> 🎯🌤\n\n"
        "• Точность радара осадков теперь привязана к координатам вашего района.\n"
        "• Бот предупредит вас за 20–30 минут, когда туча будет подходить именно к вашей локации!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.message(StateFilter(None), F.location)
async def handle_user_location(message: types.Message):
    """Handles native Telegram location sharing when user is in main menu (no active sub-mode)."""
    user_id = message.from_user.id
    loc = message.location
    lat = float(loc.latitude)
    lon = float(loc.longitude)

    city, district = await reverse_geocode_location(lat, lon)
    set_user_weather_config(user_id, city=city, district=district, lat=lat, lon=lon, alerts_enabled=True)

    loc_str = f"<b>{city}</b>" + (f" ({district})" if district else "")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍽 Найти рестораны рядом (1 км)", callback_data="geo_gastro_from_loc"),
                InlineKeyboardButton(text="🌤 Прогноз погоды", callback_data="w_refresh")
            ]
        ]
    )

    await message.answer(
        f"📍 <b>Геопозиция определена: {loc_str}!</b> 🛰️✨\n\n"
        f"🌐 Координаты: <code>{round(lat, 4)}, {round(lon, 4)}</code>\n"
        "Радар осадков настроен на ваш микрорайон с точностью до 100 метров!",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@router.callback_query(F.data == "geo_gastro_from_loc")
async def callback_geo_gastro_from_loc(callback: types.CallbackQuery, state: FSMContext):
    """Быстрый переход к ресторанам рядом по сохраненным координатам."""
    from modules.geo_gastro.locator import find_places
    from modules.geo_gastro.handlers import render_gastro_results, get_gastro_gps_keyboard
    
    await state.set_state(ActiveModeStates.geo_gastro_mode)
    user_id = callback.from_user.id
    config = get_user_weather_config(user_id)
    lat = config.get("lat")
    lon = config.get("lon")
    
    await callback.answer("🔍 Сканирую рестораны рядом...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    # Send GPS keyboard so user can easily search again
    await callback.message.answer("🍽 <b>Переключаюсь в режим «Гастро-Локатор»:</b>", parse_mode=ParseMode.HTML, reply_markup=get_gastro_gps_keyboard())
    res = await find_places(user_id, "рядом со мной", lat=lat, lon=lon, category="all")
    await render_gastro_results(callback.message, res)


@router.callback_query(F.data == "w_refresh")
async def callback_weather_refresh(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    config = get_user_weather_config(user_id)
    city = config.get("city", "Санкт-Петербург")
    district = config.get("district", "")
    lat = config.get("lat", 59.9386)
    lon = config.get("lon", 30.3141)

    success, report = await get_weather_report(city, district, lat, lon)
    if success:
        alerts_on = config.get("alerts_enabled", True)
        try:
            await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=get_weather_keyboard(alerts_on))
        except Exception:
            pass
    await callback.answer("Прогноз обновлён!")


@router.callback_query(F.data == "w_toggle_alert")
async def callback_toggle_alert(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    config = get_user_weather_config(user_id)
    new_state = not config.get("alerts_enabled", True)
    
    set_user_weather_config(
        user_id,
        city=config.get("city", "Санкт-Петербург"),
        district=config.get("district", ""),
        lat=config.get("lat", 59.9386),
        lon=config.get("lon", 30.3141),
        alerts_enabled=new_state
    )

    state_word = "включены 🔔" if new_state else "выключены 🔕"
    await callback.answer(f"Алерты осадков {state_word}")
    await callback.message.edit_reply_markup(reply_markup=get_weather_keyboard(new_state))


@router.callback_query(F.data == "w_city_help")
async def callback_city_help(callback: types.CallbackQuery):
    await callback.message.answer(
        "🏙 <b>Как задать район или город:</b>\n\n"
        "1. Отправьте команду текстом:\n"
        "<code>/set_city Санкт-Петербург, Приморский район</code>\n"
        "<i>(или <code>/set_city Москва, Хамовники</code>)</i>\n\n"
        "2. 📍 <b>Или отправьте вашу геопозицию (геолокацию)</b> через скрепку 📎 в Telegram — бот сам определит точный район!",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()
