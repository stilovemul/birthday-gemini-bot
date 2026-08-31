import re
import json
import logging
from typing import Dict, Any, List
from core.gemini import ask_gemini

logger = logging.getLogger("GamesFreebies")


async def get_active_games_freebies(user_id: int) -> Dict[str, Any]:
    """
    Returns current active 100% free game giveaways from Epic Games Store, Steam, GOG.
    """
    prompt = (
        "Сформируй подборку текущих и постоянных бесплатных раздач игр (100% скидка / Free to keep) "
        "в Epic Games Store, Steam, GOG и Prime Gaming.\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "free_games": [\n'
        '    {\n'
        '      "platform": "Epic Games Store (EGS)",\n'
        '      "title": "Еженедельная бесплатная игра EGS",\n'
        '      "original_price": "1 999 ₽ -> 0 ₽",\n'
        '      "link": "https://store.epicgames.com/free-games",\n'
        '      "description": "Новая игра каждую неделю по четвергам в 18:00 MSK (навсегда на аккаунт)."\n'
        '    },\n'
        '    {\n'
        '      "platform": "Steam",\n'
        '      "title": "Временные 100% скидки и F2P жемчужины",\n'
        '      "original_price": "Бесплатно",\n'
        '      "link": "https://store.steampowered.com/genre/Free%20to%20Play/",\n'
        '      "description": "Раздачи промо-ключей, инди-хиты и бесплатные выходные в Steam."\n'
        '    },\n'
        '    {\n'
        '      "platform": "GOG (Good Old Games)",\n'
        '      "title": "GOG Free Games Collection",\n'
        '      "original_price": "DRM-Free 0 ₽",\n'
        '      "link": "https://www.gog.com/partner/free_games",\n'
        '      "description": "Классические культовые игры без DRM-защиты навсегда в вашу библиотеку."\n'
        '    }\n'
        '  ],\n'
        '  "gamer_tip": "🎮 Совет: забирайте игры в EGS даже через браузер на смартфоне — они останутся на аккаунте навсегда!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing games JSON: {e}")

    return {
        "free_games": [
            {"platform": "Epic Games Store", "title": "Еженедельная раздача EGS", "original_price": "0 ₽", "link": "https://store.epicgames.com", "description": "Обновляется каждый четверг в 18:00 MSK"}
        ],
        "gamer_tip": "Проверяйте раздачи каждый четверг."
    }
