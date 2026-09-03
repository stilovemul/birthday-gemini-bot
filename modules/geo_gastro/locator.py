import re
import json
import logging
import urllib.parse
import aiohttp
from typing import Dict, Any, Optional, List

from core.gemini import ask_gemini
from modules.geo_gastro.storage import (
    get_seen_places,
    add_seen_places,
    save_user_gastro_context,
    get_user_gastro_context
)

logger = logging.getLogger("GeoGastroLocator")


async def reverse_geocode_detailed(lat: float, lon: float) -> Dict[str, str]:
    """Resolves GPS coordinates to detailed human-readable address components."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1&accept-language=ru"
    headers = {"User-Agent": "AiGemGastroLocator/2.0 (oleg.urinev@yandex.ru)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    addr = data.get("address", {})
                    city = addr.get("city") or addr.get("town") or addr.get("state") or "Санкт-Петербург"
                    suburb = addr.get("suburb") or ""
                    city_district = addr.get("city_district") or addr.get("borough") or addr.get("neighbourhood") or ""
                    road = addr.get("road") or ""
                    
                    # Combine neighborhood & district
                    district_parts = [p for p in [suburb, city_district] if p]
                    district = " / ".join(district_parts) if district_parts else "Центральный район"
                    
                    display = data.get("display_name", "")
                    return {
                        "city": city,
                        "district": district,
                        "road": road,
                        "display": display
                    }
    except Exception as e:
        logger.warning(f"Reverse geocode detailed error: {e}")

    return {
        "city": "Санкт-Петербург",
        "district": "Приморский район / Каменка",
        "road": "Комендантский пр.",
        "display": "Санкт-Петербург"
    }


async def find_places(
    user_id: int,
    query_or_city: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    is_speakeasy: bool = False,
    category: str = "all",
    is_more: bool = False
) -> Dict[str, Any]:
    """
    Finds top verified restaurants, cafes, bars, and bistros near user GPS or query.
    Incorporates detailed neighborhood reverse geocoding, anti-duplicate memory, and Yandex Maps links.
    """
    ctx = get_user_gastro_context(user_id)
    
    # If coordinates not passed directly, but available in context and user asks for more
    if lat is None and lon is None and ctx.get("last_lat") and ctx.get("last_lon") and (is_more or "рядом" in query_or_city.lower()):
        lat = ctx.get("last_lat")
        lon = ctx.get("last_lon")

    city = "Санкт-Петербург"
    district = ""
    road = ""
    human_location = query_or_city

    if lat is not None and lon is not None:
        geo_info = await reverse_geocode_detailed(lat, lon)
        city = geo_info["city"]
        district = geo_info["district"]
        road = geo_info["road"]
        
        loc_desc = f"{city}"
        if district:
            loc_desc += f", {district}"
        if road:
            loc_desc += f" (рядом с {road})"
        human_location = loc_desc
        
        # Auto-sync user coordinates into weather radar config
        try:
            from modules.weather_synoptic.storage import set_user_weather_config
            set_user_weather_config(user_id, city=city, district=district, lat=lat, lon=lon, alerts_enabled=True)
        except Exception as e:
            logger.warning(f"Could not auto-sync weather config: {e}")
        
        save_user_gastro_context(
            user_id,
            lat=lat,
            lon=lon,
            address=human_location,
            query=query_or_city,
            category=category
        )
    else:
        save_user_gastro_context(
            user_id,
            query=query_or_city,
            category=category
        )

    # Categories
    cat_descriptions = {
        "meat": "Топовые мясные рестораны, сочные стейки, техасский смокер, рёбра и бургеры",
        "speakeasy": "Секретные спикизи-бары (Speakeasy) с тайными входами, авторскими коктейлями и уникальной атмосферой",
        "italian": "Уютная итальянская кухня, неаполитанская пицца из дровяной печи, домашняя паста ручной работы",
        "asian": "Азиатская кухня, наваристые рамены, том ям, аутентичные суши, вок и димсамы",
        "coffee": "Спешелти кофейни с фильтр-кофе, выпечкой и сытными завтраками весь день",
        "nsk": "Легендарные рестораны и бары Новосибирска (ул. Ленина, Красный проспект)",
        "all": "Выдающиеся рестораны, гастробары и атмосферные заведения с честным высоким рейтингом"
    }
    cat_desc = cat_descriptions.get(category, cat_descriptions["all"])
    if is_speakeasy:
        cat_desc = cat_descriptions["speakeasy"]

    seen = get_seen_places(user_id)
    seen_filter = ""
    if seen:
        seen_filter = f"\n🚫 ВНИМАНИЕ: Пользователь уже знает следующие заведения, НЕ предлагай их повторно: {', '.join(seen[:30])}."

    geo_hint = ""
    if lat is not None and lon is not None:
        geo_hint = (
            f"Точная локация: {human_location}. Координаты GPS: {round(lat, 5)}, {round(lon, 5)}.\n"
            f"Ищи заведения СТРОГО в этом районе или ближайшей доступности (в радиусе 1-2 км, на соседних улицах, в ТЦ поблизости)."
        )
    else:
        geo_hint = f"Локация / Запрос: '{query_or_city}' (Город: {city})."

    prompt = f"""Ты — первоклассный ресторанный критик и сомелье.
Твоя задача — подобрать 3-4 РЕАЛЬНО существующих, проверенных заведения (куда действительно вкусно, высокий уровень сервиса и честный рейтинг 4.7+).

{geo_hint}
Направление кухни: {cat_desc}.{seen_filter}

ВАЖНО:
1. Заведения должны быть РЕАЛЬНЫМИ и находиться именно в указанном районе/городе.
2. Для каждого заведения укажи реальную пешую или авто-доступность (например: «🚶‍♂️ ~500 м (6 мин пешком)» или «🚗 ~1.5 км»).
3. Обязательно укажи точный адрес, коронные блюда и фишку заведения (для спикизи — секрет входа: тайная дверь, шкаф, звонок).

СТРУКТУРА JSON:
{{
  "search_summary": "Краткое резюме подборки (например: Топ заведений в Каменке / Комендантский)",
  "places": [
    {{
      "name": "Название заведения",
      "type": "Концепция (Мясной ресторан, Итальянская остерия, Спикизи-бар)",
      "rating": "⭐️ 4.9 (Яндекс Карты)",
      "avg_bill": "1 500 – 2 500 ₽",
      "distance": "🚶‍♂️ ~400 м (5 мин пешком)",
      "signature_dishes": "2-3 коронных блюда/напитка",
      "vibe_description": "Атмосфера, интерьер, фишка и почему стоит зайти",
      "address": "Точный адрес (ул. ..., д. ...)"
    }}
  ],
  "sommelier_tip": "Экспертный совет сомелье (по напиткам к блюдам, брони столика, лучшему времени)"
}}
"""
    resp = await ask_gemini(user_id, prompt)
    
    parsed_res = None
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            parsed_res = json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing gastro JSON: {e}")

    if not parsed_res or not parsed_res.get("places"):
        # Fallback places
        parsed_res = {
            "search_summary": f"Рекомендованные заведения ({human_location})",
            "places": [
                {
                    "name": "Meat Coin Country Club",
                    "type": "Премиальный стейк-хаус",
                    "rating": "⭐️ 4.8 (Яндекс Карты)",
                    "avg_bill": "3 000 – 4 500 ₽",
                    "distance": "🚗 ~2 км",
                    "signature_dishes": "Стейк Даллас, тартар из говядины, фирменный бургер",
                    "vibe_description": "Брутальный лофт, высочайший уровень мясной кухни и безупречный сервис.",
                    "address": "ул. Береговая, 19А"
                },
                {
                    "name": "Токио City",
                    "type": "Универсальный ресторан и гриль",
                    "rating": "⭐️ 4.6 (Яндекс Карты)",
                    "avg_bill": "1 200 – 1 800 ₽",
                    "distance": "🚶‍♂️ ~700 м",
                    "signature_dishes": "Стейк из лосося, пицца 4 сыра, теплые роллы",
                    "vibe_description": "Проверенная классика в шаговой доступности для быстрого и сытного ужина.",
                    "address": "Комендантский пр., 58"
                }
            ],
            "sommelier_tip": "Рекомендуем бронировать столик заранее в вечернее время пятницы и выходных."
        }

    # Add Yandex Maps URLs and memorize places
    places = parsed_res.get("places", [])
    for p in places:
        name = p.get("name", "")
        addr = p.get("address", "")
        query_text = f"{city} {name} {addr}".strip()
        encoded = urllib.parse.quote(query_text)
        p["map_url"] = f"https://yandex.ru/maps/?text={encoded}"

    add_seen_places(user_id, places)
    parsed_res["human_location"] = human_location
    parsed_res["lat"] = lat
    parsed_res["lon"] = lon
    parsed_res["category"] = category
    return parsed_res
