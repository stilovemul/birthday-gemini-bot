import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("GamesFreebies")


async def get_active_games_freebies(user_id: int, query: str = "") -> Dict[str, Any]:
    """
    Returns games, deals, and freebies strictly for PlayStation 5 (PS5) and PS Plus.
    """
    prompt = (
        f"Ты эксперт по экосистеме Sony PlayStation 5 (PS5). "
        f"Пользователя интересуют ИСКЛЮЧИТЕЛЬНО игры, раздачи, скидки и подписки для консоли PS5. "
        f"Запрос пользователя: '{query if query else 'актуальные раздачи и подписки PS5'}'\n\n"
        "Сформируй сводку актуальных бесплатных игр месяца по подписке PS Plus (Essential, Extra, Deluxe), "
        "лучших Free-to-Play хитов для PS5 с поддержкой DualSense и 60/120 FPS, а также скидок в PS Store.\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "ps5_deals": [\n'
        '    {\n'
        '      "category": "🎁 PS Plus Игры месяца (Essential)",\n'
        '      "title": "Ежемесячные игры по подписке PS Plus",\n'
        '      "price": "0 ₽ по подписке (навсегда)",\n'
        '      "description": "3 полноценные игры для PS5/PS4, которые обновляются в первый вторник каждого месяца.",\n'
        '      "link": "https://store.playstation.com/psplus"\n'
        '    },\n'
        '    {\n'
        '      "category": "🌟 Каталог PS Plus Extra / Deluxe",\n'
        '      "title": "Библиотека 400+ игр с оптимизацией под PS5",\n'
        '      "price": "Включено в подписку",\n'
        '      "description": "Топовые эксклюзивы: Demon\'s Souls, Returnal, Spider-Man: Miles Morales, Ghost of Tsushima DC, Death Stranding.",\n'
        '      "link": "https://store.playstation.com/pages/psplus"\n'
        '    },\n'
        '    {\n'
        '      "category": "⚡️ Топ Free-to-Play для PS5 (Без подписки)",\n'
        '      "title": "Бесплатные игры нового поколения",\n'
        '      "price": "100% Free",\n'
        '      "description": "The First Descendant (Unreal Engine 5), Genshin Impact (4K/60fps), Fortnite (120fps), Apex Legends, Warframe, Warzone.",\n'
        '      "link": "https://store.playstation.com/category/f2p"\n'
        '    },\n'
        '    {\n'
        '      "category": "🏷 Распродажи в PS Store",\n'
        '      "title": "Сезонные скидки до 75% на хиты PS5",\n'
        '      "price": "Скидки до -75%",\n'
        '      "description": "Крупные распродажи в турецком/польском/индийском PS Store с выгодной покупкой через карты пополнения.",\n'
        '      "link": "https://store.playstation.com/deals"\n'
        '    }\n'
        '  ],\n'
        '  "ps5_tip": "🎮 Лайфхак для PS5: добавляйте игры месяца в библиотеку через мобильное приложение PlayStation App — тогда они останутся на вашем аккаунте навсегда!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing PS5 JSON: {e}")

    return {
        "ps5_deals": [
            {
                "category": "🎁 PS Plus Игры месяца",
                "title": "Ежемесячные игры PS Plus для PS5",
                "price": "0 ₽ по подписке",
                "description": "Бесплатные игры каждого месяца для PS5",
                "link": "https://store.playstation.com/psplus"
            },
            {
                "category": "⚡️ Free-to-Play хиты",
                "title": "Genshin Impact, Fortnite, Warframe, The First Descendant",
                "price": "100% Free",
                "description": "Бесплатные игры с графикой нового поколения для PS5",
                "link": "https://store.playstation.com"
            }
        ],
        "ps5_tip": "Добавляйте игры в библиотеку через приложение PS App."
    }
