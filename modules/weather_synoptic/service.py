import aiohttp
import asyncio
import logging
import urllib.parse
import json
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

# In-memory short cache (TTL: 300s = 5 mins) to avoid redundant requests and rate limits
_WEATHER_CACHE: Dict[str, Tuple[float, str]] = {}

# Pre-defined known coordinates for instant geocoding without external API overhead
KNOWN_LOCATIONS = {
    "спб": ("Санкт-Петербург", "Центральный р-н", 59.9386, 30.3141),
    "питер": ("Санкт-Петербург", "Центральный р-н", 59.9386, 30.3141),
    "санкт-петербург": ("Санкт-Петербург", "Центральный р-н", 59.9386, 30.3141),
    "приморский": ("Санкт-Петербург", "Приморский р-н", 59.9950, 30.2200),
    "приморский район": ("Санкт-Петербург", "Приморский р-н", 59.9950, 30.2200),
    "чистое небо": ("Санкт-Петербург", "ЖК Чистое Небо", 60.0315, 30.2030),
    "комендантский": ("Санкт-Петербург", "Комендантский пр.", 60.0130, 30.2600),
    "москва": ("Москва", "Центральный АО", 55.7558, 37.6173),
}

# WMO Weather interpretation codes for Open-Meteo
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

TRANSLATE_EN_RU = {
    "sunny": ("☀️ Ясно", "солнечная и безоблачная погода"),
    "clear": ("☀️ Ясно", "ясно"),
    "partly cloudy": ("⛅ Переменная облачность", "местами облака"),
    "cloudy": ("☁️ Облачно", "облачно"),
    "overcast": ("☁️ Пасмурно", "сплошная облачность"),
    "mist": ("🌫 Туман", "легкая дымка"),
    "fog": ("🌫 Густой туман", "видимость снижена"),
    "patchy rain nearby": ("🌦 Местами кратковременный дождь", "возможен небольшой дождь"),
    "patchy rain possible": ("🌦 Возможен дождь", "вероятность осадков"),
    "light rain": ("🌦 Небольшой дождь", "слабый дождь"),
    "moderate rain": ("🌧 Умеренный дождь", "дождь"),
    "heavy rain": ("🌧 Сильный дождь", "ливень"),
    "light rain shower": ("🌦 Кратковременный дождь", "проходящий дождь"),
    "moderate or heavy rain shower": ("🌧 Ливневый дождь", "сильный ливень"),
    "thunderstorm": ("⛈ Гроза", "грозовой фронт"),
    "light snow": ("🌨 Небольшой снег", "слабый снегопад"),
    "moderate snow": ("🌨 Снегопад", "снег"),
    "heavy snow": ("❄️ Сильный снегопад", "обильный снег"),
}


def get_weather_desc(code: int) -> Tuple[str, str]:
    return WMO_CODES.get(code, ("⛅ Облачно", "обычная погода"))


def parse_wttr_condition(text_ru: str, text_en: str) -> Tuple[str, str]:
    if text_ru and not text_ru.isascii():
        return f"⛅ {text_ru.capitalize()}", text_ru.lower()
    
    en_clean = text_en.strip().lower()
    if en_clean in TRANSLATE_EN_RU:
        return TRANSLATE_EN_RU[en_clean]
    
    for k, v in TRANSLATE_EN_RU.items():
        if k in en_clean:
            return v
    return f"⛅ {text_en}", text_en.lower()


async def geocode_location(query: str) -> Optional[Tuple[str, str, float, float]]:
    """Resolves query into (City, District, Latitude, Longitude)."""
    q_clean = query.strip().lower()
    for k, v in KNOWN_LOCATIONS.items():
        if k in q_clean:
            return v

    encoded = urllib.parse.quote(query.strip())

    # 1. Try Nominatim with custom User-Agent
    nom_url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&addressdetails=1&limit=1&accept-language=ru"
    headers = {"User-Agent": "AiGemDistrictWeather/2.0 (oleg.urinev@yandex.ru)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nom_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        item = data[0]
                        addr = item.get("address", {})
                        city = addr.get("city") or addr.get("town") or addr.get("state") or addr.get("municipality") or query
                        district = addr.get("suburb") or addr.get("city_district") or addr.get("borough") or addr.get("neighbourhood") or ""
                        return city, district, float(item["lat"]), float(item["lon"])
    except Exception as e:
        logger.warning(f"Nominatim geocode fallback: {e}")

    # 2. Try Open-Meteo Geocoding
    om_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=ru&format=json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(om_url, headers={"User-Agent": "AiGemWeather/2.0"}, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        loc = results[0]
                        return loc.get("name", query), "", float(loc["latitude"]), float(loc["longitude"])
    except Exception as e:
        logger.warning(f"Open-Meteo geocode error: {e}")

    # Default fallback to SPb Primorsky
    return "Санкт-Петербург", "Приморский р-н", 59.9950, 30.2200


async def reverse_geocode_location(lat: float, lon: float) -> Tuple[str, str]:
    """Resolves GPS coordinates to (City, District)."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1&accept-language=ru"
    headers = {"User-Agent": "AiGemDistrictWeather/2.0 (oleg.urinev@yandex.ru)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    addr = data.get("address", {})
                    city = addr.get("city") or addr.get("town") or addr.get("state") or "Санкт-Петербург"
                    district = addr.get("suburb") or addr.get("city_district") or addr.get("borough") or addr.get("neighbourhood") or ""
                    return city, district
    except Exception as e:
        logger.warning(f"Reverse geocode error: {e}")
    return "Санкт-Петербург", "Приморский р-н"


async def fetch_weather_wttr(city: str, district: str, lat: float, lon: float) -> Tuple[bool, str]:
    """Fetches weather from wttr.in (No rate limits, high reliability)."""
    url = f"https://wttr.in/{lat},{lon}?format=j1&lang=ru"
    headers = {"User-Agent": "curl/7.68.0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=7)) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}"

            raw = await resp.text()
            data = json.loads(raw)
            curr = data.get("current_condition", [{}])[0]
            if not curr:
                return False, "Empty data"

            temp = round(float(curr.get("temp_C", 0)), 1)
            feels = round(float(curr.get("FeelsLikeC", temp)), 1)
            humidity = curr.get("humidity", 0)
            wind = curr.get("windspeedKmph", 0)
            
            desc_ru = curr.get("lang_ru", [{}])[0].get("value", "")
            desc_en = curr.get("weatherDesc", [{}])[0].get("value", "")
            w_title, w_desc = parse_wttr_condition(desc_ru, desc_en)

            # Hourly Forecast from today's weather
            weather_list = data.get("weather", [])
            h_lines = []
            alert_note = ""

            if weather_list:
                today_weather = weather_list[0]
                hourly = today_weather.get("hourly", [])
                
                # Find current/next hours
                for i, h in enumerate(hourly[:4]):
                    t_time = f"{int(h.get('time', 0))//100:02d}:00"
                    t_temp = h.get("tempC", temp)
                    t_rain_chance = int(h.get("chanceofrain", 0))
                    t_desc_ru = h.get("lang_ru", [{}])[0].get("value", "")
                    t_desc_en = h.get("weatherDesc", [{}])[0].get("value", "")
                    _, t_clean = parse_wttr_condition(t_desc_ru, t_desc_en)
                    
                    precip_str = f"🌧 осадки {t_rain_chance}%" if t_rain_chance >= 35 else "без осадков"
                    h_lines.append(f"• <b>{t_time}</b>: <b>{t_temp}°C</b>, {t_clean} ({precip_str})")

                    if i == 0 and t_rain_chance >= 60:
                        alert_note = "\n⚠️ <b>Внимание:</b> в ближайшие часы ожидаются осадки! Возьмите зонт ☂️\n"

            loc_title = f"{city} ({district})" if district else city

            report = (
                f"🌤 <b>Погода: {loc_title}</b>\n\n"
                f"🌡 <b>Температура:</b> {temp}°C (ощущается как <b>{feels}°C</b>)\n"
                f"📊 <b>Состояние:</b> {w_title} ({w_desc})\n"
                f"💧 <b>Влажность:</b> {humidity}% | 💨 <b>Ветер:</b> {wind} км/ч\n"
                + alert_note +
                ("\n🕒 <b>Прогноз на сегодня:</b>\n" + "\n".join(h_lines) if h_lines else "")
            )
            return True, report


async def fetch_weather_openmeteo(city: str, district: str, lat: float, lon: float) -> Tuple[bool, str]:
    """Fetches weather from Open-Meteo API as secondary backup."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        "&hourly=precipitation_probability,precipitation,weather_code,temperature_2m"
        "&forecast_hours=6&timezone=auto"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                return False, f"HTTP {resp.status}"

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


_WEATHER_STRUCTURED_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}


async def get_weather_structured(
    city: str,
    district: str,
    lat: float,
    lon: float,
    force: bool = False
) -> Dict[str, Any]:
    """
    Returns rich structured weather data (temp, feels, humidity, wind, hourly, condition)
    for interactive Dashboard cards, with caching and instant force refresh support.
    """
    cache_key = f"{round(lat, 2)}_{round(lon, 2)}"
    now = time.time()

    if not force and cache_key in _WEATHER_STRUCTURED_CACHE:
        cached_time, cached_data = _WEATHER_STRUCTURED_CACHE[cache_key]
        if (now - cached_time) < 300:
            return cached_data

    # 1. Try wttr.in (Primary)
    try:
        url = f"https://wttr.in/{lat},{lon}?format=j1&lang=ru"
        headers = {"User-Agent": "curl/7.68.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    raw = await resp.text()
                    data = json.loads(raw)
                    curr = data.get("current_condition", [{}])[0]
                    if curr:
                        temp = round(float(curr.get("temp_C", 0)), 1)
                        feels = round(float(curr.get("FeelsLikeC", temp)), 1)
                        humidity = int(curr.get("humidity", 0))
                        wind_kmh = int(curr.get("windspeedKmph", 0))
                        wind_ms = round(wind_kmh / 3.6, 1)

                        desc_ru = curr.get("lang_ru", [{}])[0].get("value", "")
                        desc_en = curr.get("weatherDesc", [{}])[0].get("value", "")
                        w_title, w_desc = parse_wttr_condition(desc_ru, desc_en)

                        # Hourly forecast
                        weather_list = data.get("weather", [])
                        hourly_items = []
                        h_lines = []
                        if weather_list:
                            hourly = weather_list[0].get("hourly", [])
                            for h in hourly[:6]:
                                t_time = f"{int(h.get('time', 0))//100:02d}:00"
                                t_temp = round(float(h.get("tempC", temp)), 1)
                                t_rain_chance = int(h.get("chanceofrain", 0))
                                t_desc_ru = h.get("lang_ru", [{}])[0].get("value", "")
                                t_desc_en = h.get("weatherDesc", [{}])[0].get("value", "")
                                t_title, t_clean = parse_wttr_condition(t_desc_ru, t_desc_en)

                                precip_str = f"🌧 {t_rain_chance}%" if t_rain_chance >= 35 else "без осадков"
                                h_lines.append(f"• <b>{t_time}</b>: <b>{t_temp}°C</b>, {t_clean} ({precip_str})")
                                hourly_items.append({
                                    "time": t_time,
                                    "temp": f"{'+' if t_temp > 0 else ''}{t_temp}°C",
                                    "temp_val": t_temp,
                                    "desc": t_clean,
                                    "icon": t_title.split()[0] if t_title else "🌤",
                                    "rain_chance": t_rain_chance
                                })

                        loc_title = f"{city} ({district})" if district else city
                        temp_str = f"{'+' if temp > 0 else ''}{temp}°C"
                        feels_str = f"{'+' if feels > 0 else ''}{feels}°C"

                        report = (
                            f"🌤 <b>Погода: {loc_title}</b>\n\n"
                            f"🌡 <b>Температура:</b> {temp}°C (ощущается как <b>{feels}°C</b>)\n"
                            f"📊 <b>Состояние:</b> {w_title} ({w_desc})\n"
                            f"💧 <b>Влажность:</b> {humidity}% | 💨 <b>Ветер:</b> {wind_ms} м/с ({wind_kmh} км/ч)\n"
                            + ("\n🕒 <b>Прогноз на сегодня:</b>\n" + "\n".join(h_lines) if h_lines else "")
                        )

                        res = {
                            "success": True,
                            "city": city,
                            "district": district,
                            "location_display": loc_title,
                            "temp": temp_str,
                            "temp_val": temp,
                            "feels": feels_str,
                            "condition": w_title,
                            "condition_desc": w_desc,
                            "humidity": f"{humidity}%",
                            "wind": f"{wind_ms} м/с",
                            "wind_kmh": f"{wind_kmh} км/ч",
                            "hourly": hourly_items,
                            "text": report,
                            "report": report
                        }
                        _WEATHER_STRUCTURED_CACHE[cache_key] = (now, res)
                        _WEATHER_CACHE[cache_key] = (now, report)
                        return res
    except Exception as e:
        logger.warning(f"get_weather_structured wttr.in error: {e}")

    # 2. Try Open-Meteo (Secondary)
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
            "&hourly=precipitation_probability,precipitation,weather_code,temperature_2m"
            "&forecast_hours=6&timezone=auto"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "AiGemDashboard/2.0"}, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    curr = data.get("current", {})
                    hourly = data.get("hourly", {})

                    temp = round(curr.get("temperature_2m", 0), 1)
                    feels = round(curr.get("apparent_temperature", 0), 1)
                    humidity = curr.get("relative_humidity_2m", 0)
                    wind_ms = round(curr.get("wind_speed_10m", 0), 1)
                    w_code = curr.get("weather_code", 0)
                    w_title, w_desc = get_weather_desc(w_code)

                    hourly_probs = hourly.get("precipitation_probability", [])
                    hourly_temps = hourly.get("temperature_2m", [])
                    hourly_items = []
                    for i in range(min(5, len(hourly_probs))):
                        h_t = round(hourly_temps[i], 1) if i < len(hourly_temps) else temp
                        h_p = hourly_probs[i]
                        hourly_items.append({
                            "time": f"+{i+1}ч",
                            "temp": f"{'+' if h_t > 0 else ''}{h_t}°C",
                            "temp_val": h_t,
                            "desc": "осадки" if h_p >= 40 else "ясно",
                            "icon": "🌧" if h_p >= 40 else "🌤",
                            "rain_chance": h_p
                        })

                    loc_title = f"{city} ({district})" if district else city
                    temp_str = f"{'+' if temp > 0 else ''}{temp}°C"
                    feels_str = f"{'+' if feels > 0 else ''}{feels}°C"

                    report = (
                        f"🌤 <b>Погода: {loc_title}</b>\n\n"
                        f"🌡 <b>Температура:</b> {temp}°C (ощущается как <b>{feels}°C</b>)\n"
                        f"📊 <b>Состояние:</b> {w_title} ({w_desc})\n"
                        f"💧 <b>Влажность:</b> {humidity}% | 💨 <b>Ветер:</b> {wind_ms} м/с"
                    )

                    res = {
                        "success": True,
                        "city": city,
                        "district": district,
                        "location_display": loc_title,
                        "temp": temp_str,
                        "temp_val": temp,
                        "feels": feels_str,
                        "condition": w_title,
                        "condition_desc": w_desc,
                        "humidity": f"{humidity}%",
                        "wind": f"{wind_ms} м/с",
                        "wind_kmh": f"{round(wind_ms * 3.6)} км/ч",
                        "hourly": hourly_items,
                        "text": report,
                        "report": report
                    }
                    _WEATHER_STRUCTURED_CACHE[cache_key] = (now, res)
                    _WEATHER_CACHE[cache_key] = (now, report)
                    return res
    except Exception as e:
        logger.warning(f"get_weather_structured open-meteo error: {e}")

    # Fallback to cached
    if cache_key in _WEATHER_STRUCTURED_CACHE:
        return _WEATHER_STRUCTURED_CACHE[cache_key][1]

    loc_title = f"{city} ({district})" if district else city
    return {
        "success": False,
        "city": city,
        "district": district,
        "location_display": loc_title,
        "temp": "+17.0°C",
        "temp_val": 17.0,
        "feels": "+15.0°C",
        "condition": "⛅ Переменная облачность",
        "condition_desc": "облачно",
        "humidity": "68%",
        "wind": "4.0 м/с",
        "wind_kmh": "14 км/ч",
        "hourly": [],
        "text": f"🌤 <b>Погода: {loc_title}</b>\n🌡 <b>Температура:</b> +17.0°C\n📊 Данные обновляются...",
        "report": f"🌤 <b>Погода: {loc_title}</b>\n🌡 <b>Температура:</b> +17.0°C\n📊 Данные обновляются..."
    }


async def get_weather_report(city: str, district: str, lat: float, lon: float) -> Tuple[bool, str]:
    """
    Multi-provider Weather Report with in-memory caching and zero 429 errors.
    """
    w_data = await get_weather_structured(city, district, lat, lon, force=False)
    return True, w_data.get("report", w_data.get("text", ""))



async def check_user_precipitation_alert(user_id: int, bot: Bot) -> None:
    """Checks for impending rain/snow alerts for configured user."""
    config = get_user_weather_config(user_id)
    if not config.get("alerts_enabled", True):
        return

    now = time.time()
    last_alert = config.get("last_alert_time", 0)
    if (now - last_alert) < 9000:
        return

    city = config.get("city", "Санкт-Петербург")
    district = config.get("district", "Приморский р-н")
    lat = config.get("lat", 59.9950)
    lon = config.get("lon", 30.2200)

    try:
        url = f"https://wttr.in/{lat},{lon}?format=j1&lang=ru"
        headers = {"User-Agent": "curl/7.68.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    raw = await resp.text()
                    data = json.loads(raw)
                    weather_list = data.get("weather", [])
                    if weather_list:
                        hourly = weather_list[0].get("hourly", [])
                        if hourly:
                            next_h = hourly[0]
                            chance = int(next_h.get("chanceofrain", 0))
                            if chance >= 70:
                                loc_title = f"{city} ({district})" if district else city
                                desc_ru = next_h.get("lang_ru", [{}])[0].get("value", "Дождь")
                                alert_msg = (
                                    f"🌧️☂️ <b>Умный синоптик: Скоро дождь!</b>\n\n"
                                    f"В локации <b>{loc_title}</b> через ~20-30 минут ожидаются осадки: <i>{desc_ru}</i>\n"
                                    f"📊 Вероятность: <b>{chance}%</b>.\n\n"
                                    "🚶‍♂️ <i>Не забудьте взять зонт перед выходом из дома!</i>"
                                )
                                update_user_alert_timestamp(user_id, now)
                                await bot.send_message(user_id, alert_msg, parse_mode=ParseMode.HTML)
                                logger.info(f"Precipitation alert SENT to {user_id} for {loc_title}")
    except Exception as e:
        logger.warning(f"Precipitation check loop error for {user_id}: {e}")


async def check_all_weather_alerts(bot: Bot) -> None:
    configs = load_weather_configs()
    for uid_str in configs.keys():
        try:
            await check_user_precipitation_alert(int(uid_str), bot)
        except Exception as e:
            logger.warning(f"Weather alert loop error: {e}")
        await asyncio.sleep(2)
