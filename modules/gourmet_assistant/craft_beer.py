import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("CraftBeerGuide")


async def get_craft_beer_guide(user_id: int, style_query: str = "") -> Dict[str, Any]:
    b_query = style_query if style_query else "New England IPA (NEIPA) / Молочный стаут / Саур эль с фруктами"
    prompt = (
        "Ты сертифицированный бир-сомелье (Cicerone). Составь экспертный гид по стилям крафтового пива.\n"
        f"Запрос пользователя: '{b_query}'\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "style_name": "🍺 New England IPA (Hazy / Juicy IPA)",\n'
        '  "characteristics": {\n'
        '    "abv": "6.0 - 7.5% (Крепость)",\n'
        '    "ibu": "25 - 45 IBU (Мягкая сочная горечь)",\n'
        '    "color": "Мутный соломенно-желтый, похож на свежевыжатый сок",\n'
        '    "aroma": "Взрыв тропических фруктов: манго, маракуйя, цитрусы, ананас"\n'
        '  },\n'
        '  "flavor_profile": "Невероятно шелковистое тело за счет овсяных хлопьев, яркий фруктовый вкус хмелей (Citra, Mosaic, Galaxy) без резкой горечи.",\n'
        '  "food_pairings": [\n'
        '    "🍔 Сочные бургеры и крылышки Баффало",\n'
        '    "🍕 Пицца с острой салями или сырами",\n'
        '    "🌮 Мексиканские такос и севиче"\n'
        '  ],\n'
        '  "sommelier_advice": "💡 Пейте NEIPA максимально свежим (до 2-3 месяцев с даты розлива), охлажденным до 8-10°C в бокале Тюльпан или Снифтер!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing craft beer JSON: {e}")

    return {
        "style_name": "🍺 New England IPA (NEIPA)",
        "characteristics": {
            "abv": "6.5%",
            "ibu": "35 IBU",
            "color": "Мутный золотистый",
            "aroma": "Манго, маракуйя, цитрус"
        },
        "flavor_profile": "Мягкий фруктовый вкус с шелковистой текстурой",
        "food_pairings": ["Бургеры", "Пицца", "Острые закуски"],
        "sommelier_advice": "Пейте свежим в бокале тюльпан при температуре 8-10°C!"
    }
