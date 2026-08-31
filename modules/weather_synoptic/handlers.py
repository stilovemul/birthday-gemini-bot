import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.weather_synoptic.storage import (
    get_user_weather_config,
    set_user_weather_config
)
from modules.weather_synoptic.service import (
    geocode_city,
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
                InlineKeyboardButton(text="🏙 Сменить город (/set_city)", callback_data="w_city_help")
            ]
        ]
    )


@router.message(Command("weather"))
@router.message(F.text == "🌤 Погода & Осадки")
async def cmd_weather(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    args = (message.text or "").split(maxsplit=1)

    config = get_user_weather_config(user_id)
    city = config.get("city", "Санкт-Петербург")
    lat = config.get("lat", 59.9386)
    lon = config.get("lon", 30.3141)

    if len(args) > 1 and args[1].strip() and args[1].strip() != "Погода & Осадки":
        custom_city = args[1].strip()
        geo = await geocode_city(custom_city)
        if geo:
            city, lat, lon = geo
        else:
            await message.answer(f"⚠️ Город «{custom_city}» не найден. Показываю погоду для {city}.")

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    success, report = await get_weather_report(city, lat, lon)

    if success:
        alerts_on = config.get("alerts_enabled", True)
        await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=get_weather_keyboard(alerts_on))
    else:
        await message.answer(f"❌ {report}")


@router.message(Command("set_city"))
async def cmd_set_city(message: types.Message):
    user_id = message.from_user.id
    args = (message.text or "").split(maxsplit=1)

    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "🏙 <b>Укажите ваш город:</b>\n"
            "Пример: <code>/set_city Москва</code> или <code>/set_city Екатеринбург</code>",
            parse_mode=ParseMode.HTML
        )
        return

    city_name = args[1].strip()
    geo = await geocode_city(city_name)
    if not geo:
        await message.answer(f"❌ Не удалось найти город «{city_name}». Проверьте написание.")
        return

    real_name, lat, lon = geo
    set_user_weather_config(user_id, city=real_name, lat=lat, lon=lon, alerts_enabled=True)

    await message.answer(
        f"✅ <b>Город успешно установлен: {real_name}!</b> 🌤\n\n"
        "• Теперь при запросе погоды бот сразу покажет прогноз для вашего города.\n"
        "• Умный радар осадков будет предупреждать вас за 20–30 минут до начала дождя!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "w_refresh")
async def callback_weather_refresh(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    config = get_user_weather_config(user_id)
    city = config.get("city", "Санкт-Петербург")
    lat = config.get("lat", 59.9386)
    lon = config.get("lon", 30.3141)

    success, report = await get_weather_report(city, lat, lon)
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
        "🏙 <b>Чтобы сменить город по умолчанию</b>, отправьте команду:\n"
        "<code>/set_city НазваниеГорода</code>\n\n"
        "<i>Например: <code>/set_city Москва</code>, <code>/set_city Сочи</code>, <code>/set_city Казань</code></i>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()
