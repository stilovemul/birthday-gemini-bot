import aiohttp
import asyncio
import logging
import urllib.parse
import time
from typing import Dict, Any, Optional, Tuple, List
from aiogram import Bot
from aiogram.enums import ParseMode

from modules.weather_synoptic.storage import (
    load_weather_configs,
    get_user_weather_config,
    set_user_weather_config,
    update_user_alert_timestamp
)

logger = logging.getLogger("WeatherService")

# WMO Weather interpretation codes
WMO_CODES = {
    0: ("☀️ Ясно", "солнечная и безоблачная погода"),
    1: ("🌤 В основном ясно", "небольшая облачность"),
    2: ("⛅ Переменная облачность", "местами облака"),
    3: ("☁️ Пасмурно", "сплошная облачность"),
    45: ("🌫 Туман", "видимость снижена"),
    48: ("🌫 Изморозь", "туман с оседанием изморози"),
    51: ("🌦 Легкая морось", "мелкий моросящий дождь"),
    53: ("🌧 Умеренная морось", "моросящий дождь"),
    55: ("🌧 Плотная морось", "сильная морось"),
    61: ("🌦 Небольшой дождь", "кратковременный слабый дождь"),
    63: ("🌧 Умеренный дождь", "дождь"),
    65: ("🌧 Сильный ливень", "интенсивный дождь"),
    71: ("🌨 Небольшой снег", "легкий снегопад"),
    73: ("🌨 Умеренный снег", "снегопад"),
    75: ("❄️ Сильный снегопад", "обильный снег"),
    80: ("🌦 Ливневый дождь", "ливень с прояснениями"),
    81: ("🌧 Сильный ливень", "сильные осадки"),
    82: ("⛈ Шквалистый ливень", "очень сильный дождь"),
    95: ("⛈ Гроза", "грозовой фронт"),
    96: ("⛈ Гроза с градом", "гроза и град")
}


def get_weather_desc(code: int) -> Tuple[str, str]:
    return WMO_CODES.get(code, ("⛅ Облачно", "обычная погода"))


async def geocode_location(query: str) -> Optional[Tuple[str, str, float, float]]:
    """
    Resolves query (e.g. 'СПб Приморский район' or 'Москва Раменки') into:
    (City, District, Latitude, Longitude)
    """
    encoded = urllib.parse.quote(query.strip())
    # 1. First try Nominatim for hyper-accurate district resolution
    nom_url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&addressdetails=1&limit=1&accept-language=ru"
    headers = {"User-Agent": "AiGemDistrictWeather/1.0 (oleg.urinev@yandex.ru)"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nom_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        item = data[0]
                        addr = item.get("address", {})
                        city = addr.get("city") or addr.get("town") or addr.get("state") or addr.get("municipality") or query
                        district = addr.get("suburb") or addr.get("city_district") or addr.get("borough") or addr.get("neighbourhood") or ""
                        lat = float(item["lat"])
                        lon = float(item["lon"])
                        return city, district, lat, lon
    except Exception as e:
        logger.warning(f"Nominatim lookup failed: {e}")

    # 2. Fallback to Open-Meteo Geocoding
    om_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=ru&format=json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(om_url, headers={"User-Agent": "AiGemWeather/1.0"}, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        loc = results[0]
                        return loc.get("name", query), "", float(loc["latitude"]), float(loc["longitude"])
    except Exception as e:
        logger.error(f"Open-Meteo geocode fallback error: {e}")

    return None


async def reverse_geocode_location(lat: float, lon: float) -> Tuple[str, str]:
    """Resolves GPS coordinates to (City, District)."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1&accept-language=ru"
    headers = {"User-Agent": "AiGemDistrictWeather/1.0 (oleg.urinev@yandex.ru)"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    addr = data.get("address", {})
                    city = addr.get("city") or addr.get("town") or addr.get("state") or "Мой город"
                    district = addr.get("suburb") or addr.get("city_district") or addr.get("borough") or addr.get("neighbourhood") or ""
                    return city, district
    except Exception as e:
        logger.error(f"Reverse geocode error: {e}")
    return "Моё местоположение", ""


async def get_weather_report(city: str, district: str, lat: float, lon: float) -> Tuple[bool, str]:
    """Fetches full current weather + hourly forecast for specific district coordinates."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        "&hourly=precipitation_probability,precipitation,weather_code,temperature_2m"
        "&forecast_hours=6&timezone=auto"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return False, f"Ошибка метеосервера: HTTP {resp.status}"

                data = await resp.json()
                curr = data.get("current", {})
                hourly = data.get("hourly", {})

                temp = round(curr.get("temperature_2m", 0), 1)
                feels = round(curr.get("apparent_temperature", 0), 1)
                humidity = curr.get("relative_humidity_2m", 0)
                wind = round(curr.get("wind_speed_10m", 0), 1)
                w_code = curr.get("weather_code", 0)
                cur_precip = curr.get("precipitation", 0)

                w_title, w_desc = get_weather_desc(w_code)

                # Hourly forecast
                hourly_probs = hourly.get("precipitation_probability", [])
                hourly_precip = hourly.get("precipitation", [])
                hourly_temps = hourly.get("temperature_2m", [])

                h_lines = []
                for i in range(min(4, len(hourly_probs))):
                    h_t = round(hourly_temps[i], 1) if i < len(hourly_temps) else temp
                    h_prob = hourly_probs[i]
                    p_val = hourly_precip[i] if i < len(hourly_precip) else 0
                    precip_str = f"🌧 {p_val}мм ({h_prob}%)" if h_prob >= 30 else "без осадков"
                    h_lines.append(f"+{i+1}ч: <b>{h_t}°C</b>, {precip_str}")

                # Alert insight
                alert_note = ""
                if hourly_probs and hourly_probs[0] >= 60:
                    alert_note = "\n⚠️ <b>Внимание:</b> в ближайший час в вашем районе ожидаются осадки! Возьмите зонт ☂️\n"
                elif cur_precip > 0:
                    alert_note = "\n🌧 <b>Сейчас на улице идут осадки.</b>\n"

                loc_title = f"{city} ({district})" if district else city

                report = (
                    f"🌤 <b>Погода: {loc_title}</b>\n\n"
                    f"🌡 <b>Температура:</b> {temp}°C (ощущается как <b>{feels}°C</b>)\n"
                    f"📊 <b>Состояние:</b> {w_title} ({w_desc})\n"
                    f"💧 <b>Влажность:</b> {humidity}% | 💨 <b>Ветер:</b> {wind} км/ч\n"
                    + alert_note +
                    "\n🕒 <b>Прогноз по часам в районе:</b>\n"
                    + "\n".join(h_lines)
                )
                return True, report

    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return False, f"Ошибка получения погоды: {e}"


async def check_user_precipitation_alert(user_id: int, bot: Bot) -> None:
    """Checks if rain/snow is starting in user's specific district and fires alert."""
    config = get_user_weather_config(user_id)
    if not config.get("alerts_enabled", True):
        return

    now = time.time()
    last_alert = config.get("last_alert_time", 0)
    # Alert cooldown: 2.5 hours (9000s)
    if (now - last_alert) < 9000:
        return

    city = config.get("city", "Санкт-Петербург")
    district = config.get("district", "")
    lat = config.get("lat", 59.9386)
    lon = config.get("lon", 30.3141)

    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=precipitation,weather_code"
        "&hourly=precipitation_probability,precipitation,weather_code"
        "&forecast_hours=2&timezone=auto"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    curr = data.get("current", {})
                    hourly = data.get("hourly", {})
                    probs = hourly.get("precipitation_probability", [])
                    precips = hourly.get("precipitation", [])

                    cur_rain = curr.get("precipitation", 0)
                    next_hour_prob = probs[0] if probs else 0
                    next_precip = precips[0] if precips else 0

                    if (next_hour_prob >= 65 or next_precip >= 0.4) and cur_rain < 0.2:
                        w_code = hourly.get("weather_code", [61])[0]
                        w_title, _ = get_weather_desc(w_code)
                        loc_title = f"{city} ({district})" if district else city

                        alert_msg = (
                            f"🌧️☂️ <b>Умный синоптик: Скоро дождь!</b>\n\n"
                            f"В локации <b>{loc_title}</b> через ~20-30 минут ожидаются осадки: {w_title}\n"
                            f"📊 Вероятность: <b>{next_hour_prob}%</b> (до {next_precip} мм).\n\n"
                            "🚶‍♂️ <i>Не забудьте взять зонт перед выходом из дома!</i>"
                        )
                        update_user_alert_timestamp(user_id, now)
                        await bot.send_message(user_id, alert_msg, parse_mode=ParseMode.HTML)
                        logger.info(f"Precipitation alert SENT to user {user_id} for {loc_title}")

    except Exception as e:
        logger.warning(f"Error checking weather alert for user {user_id}: {e}")


async def check_all_weather_alerts(bot: Bot) -> None:
    """Iterates through all users and checks for impending precipitation."""
    configs = load_weather_configs()
    for uid_str in configs.keys():
        try:
            user_id = int(uid_str)
            await check_user_precipitation_alert(user_id, bot)
        except Exception as e:
            logger.warning(f"Weather alert loop error for {uid_str}: {e}")
        await asyncio.sleep(1.5)
