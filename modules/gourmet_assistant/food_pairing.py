import re
import json
import html
import logging
from typing import Dict, Any, Optional, List
from core.gemini import ask_gemini

logger = logging.getLogger("FoodPairingAdvisor")


def is_food_pairing_query(text: str) -> bool:
    """Detects if user is asking what to drink with a specific dish or food."""
    if not text:
        return False
    t = text.lower().strip()
    
    intent_words = [
        "кушать", "есть", "съесть", "покушать", "ужин", "обед", "завтрак", "закуск", "закусить", "закусывать",
        "под ", "к ", "с чем", "сочета", "посоветуй под", "какое пиво под", "какое вино под", "что взять к",
        "что выпить с", "что подойдет к", "что лучше к", "что пить с", "какой алкоголь к", "пара к"
    ]
    
    food_words = [
        "пицц", "стейк", "мяс", "шашлык", "бургер", "ребр", "ребрышк", "крыл", "крылышк",
        "сыр", "сырн", "кальмар", "креветк", "рыб", "суши", "ролл", "лосос", "форел", "вобл", "корюшк", "мидии",
        "паст", "карбонар", "болоньез", "лазань", "пельмен", "колбас", "сосиск", "сосисочк", "гренки",
        "чипс", "начос", "орешк", "хамон", "прошутт", "утка", "куриц", "свинин", "говядин", "баранин",
        "том ям", "вок", "рамен", "острое", "сладкое", "десерт", "шоколад", "торт", "бургеры", "тако"
    ]
    
    has_intent = any(w in t for w in intent_words)
    has_food = any(f in t for f in food_words)
    
    return (has_intent and has_food) or (has_food and any(d in t for d in ["пиво", "вино", "напиток", "алкоголь", "выпить", "взять", "посоветуй"]))


async def get_food_pairing_recommendation(
    user_id: int,
    query: str,
    active_shelf_data: Optional[Dict[str, Any]] = None,
    image_bytes: Optional[bytes] = None
) -> str:
    """
    World-class Food Pairing Sommelier recommendation:
    1. If active shelf data exists: picks the best matching bottle/can FROM THE PHOTO with exact shelf position.
    2. If no shelf photo: gives top sommelier pairing with accessible store brands, flavor chemistry, and what to avoid.
    """
    if active_shelf_data and (active_shelf_data.get("shelves") or active_shelf_data.get("top_pick")):
        shelf_json = json.dumps(active_shelf_data, ensure_ascii=False, indent=2)
        prompt = (
            "Ты мировой гранд-сомелье (Master Sommelier) и главный пивной эксперт (Master Cicerone).\n"
            "Пользователь ранее прислал ФОТО витрины магазина / холодильника.\n"
            f"ВОТ ПОЛНЫЙ СКАН ПОЛОК С ЭТОГО ФОТО:\n"
            f"```json\n{shelf_json}\n```\n\n"
            f"ЗАПРОС ПОЛЬЗОВАТЕЛЯ: «{query}»\n\n"
            "ТВОЯ ЗАДАЧА:\n"
            "1. Выбери ИДЕАЛЬНУЮ гастрономическую пару под это блюдо ИСКЛЮЧИТЕЛЬНО ИЗ БУТЫЛОК/БАНОК НА ЭТОМ ФОТО!\n"
            "2. Укажи ТОЧНУЮ полку и положение напитка (например: '2-я полка сверху, 3-я банка слева, синяя этикетка').\n"
            "3. Объясни гастрономическую химию: как именно этот хмель/солод/кислотность/танины взаимодействуют с жиром, солью, соусом или остротой блюда.\n"
            "4. Предложи альтернативный №2 вариант (тоже с этой фотографии).\n"
            "5. Укажи 1 сорт с этой витрины, который категорически НЕЛЬЗЯ брать под это блюдо (чтобы не испортить вкус).\n"
            "6. Оформи ответ в красивом Telegram HTML с понятными эмодзи и четкими блоками."
        )
        try:
            return await ask_gemini(user_id, prompt, image_bytes=image_bytes)
        except Exception as e:
            logger.error(f"Error in food pairing with shelf: {e}")

    # Case B: Free pairing without photo
    prompt = (
        "Ты сертифицированный мировой гранд-сомелье (Master Sommelier) и главный эксперт по пиву и вину (Master Cicerone).\n"
        f"Пользователь спрашивает рекомендацию напитка под еду: «{query}».\n\n"
        "Дай исчерпывающий, сочный и практичный гастрономический гид:\n\n"
        "🥇 <b>#1 ИДЕАЛЬНАЯ ПАРА (ТОП-1 ВЫБОР):</b>\n"
        "- Точный стиль напитка (пиво, вино или крепкое).\n"
        "- Конкретные доступные бренды и бутылки, которые легко купить в супермаркетах (К&Б, ВкусВилл, Перекресток, Винлаб, Ашан).\n"
        "- 👅 <i>Гастрономическая химия (почему это работает):</i> как именно кислотность, танины, хмелевая горечь или карбонизация дополняют блюдо, очищают рецепторы от жира или тушат остроту.\n\n"
        "🥈 <b>#2 АЛЬТЕРНАТИВА (ДРУГОЙ ПРОФИЛЬ):</b>\n"
        "- Более легкий или необычный вариант (например, безалкогольное, сидр или альтернативный винный сорт).\n\n"
        "🚫 <b>ЧТО КАТЕГОРИЧЕСКИ НЕ ПОДХОДИТ:</b>\n"
        "- Напиток, который испортит вкус этого блюда (например: танинное вино к острой азиатской еде или сладкий сидр к стейку) и почему.\n\n"
        "🌡 <b>ПОДАЧА:</b>\n"
        "- Идеальная температура охлаждения и форма бокала.\n\n"
        "Форматируй ответ в чистом Telegram HTML (<b>, <i>, <code>). Все термины переводи на русский язык."
    )
    try:
        return await ask_gemini(user_id, prompt)
    except Exception as e:
        logger.error(f"Error in get_food_pairing_recommendation: {e}")
        return (
            f"🍽 <b>Гастрономический совет сомелье:</b>\n\n"
            f"К вашему блюду <i>«{html.escape(query)}»</i> идеально подойдет сбалансированный сорт с выраженной свежестью. "
            f"Для жирных и мясных блюд выбирайте хмелевые IPA или сухое танинное вино (Каберне, Мальбек), а для легких закусок и морепродуктов — немецкий пилснер, пшеничное или Совиньон Блан!"
        )
