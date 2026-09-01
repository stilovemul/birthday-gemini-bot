import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from core.keyboards import get_main_menu
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
    args = (message.text or "").split(maxsplit=1)

    config = get_user_weather_config(user_id)
    city = config.get("city", "Санкт-Петербург")
    district = config.get("district", "")
    lat = config.get("lat", 59.9386)
    lon = config.get("lon", 30.3141)

    if len(args) > 1 and args[1].strip() and args[1].strip() != "Погода & Осадки":
        custom_query = args[1].strip()
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
        await message.answer(f"❌ Не удалось найти «{query}». Попробуйте написать точнее: <code>Город, Район</code>.")
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


@router.message(F.location)
async def handle_user_location(message: types.Message):
    """Handles native Telegram location sharing for pinpoint neighborhood precision."""
    user_id = message.from_user.id
    loc = message.location
    lat = float(loc.latitude)
    lon = float(loc.longitude)

    city, district = await reverse_geocode_location(lat, lon)
    set_user_weather_config(user_id, city=city, district=district, lat=lat, lon=lon, alerts_enabled=True)

    loc_str = f"<b>{city}</b>" + (f" ({district})" if district else "")

    await message.answer(
        f"📍 <b>Геопозиция определена: {loc_str}!</b> 🛰️✨\n\n"
        f"🌐 Координаты: <code>{round(lat, 4)}, {round(lon, 4)}</code>\n"
        "Радар осадков теперь настроен на ваш микрорайон с точностью до 100 метров!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


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
