import re
import json
import logging
from typing import Dict, Any, List, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("AIBarman")


async def craft_cocktail(
    user_id: int,
    bar_stock: str,
    non_alcoholic: bool = False,
    vibe: str = "вечерний чилл",
    seen_titles: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Creates cocktail recipe based on available ingredients at home.
    """
    alcol_type = "безалкогольный (mocktail)" if non_alcoholic else "авторский или классический коктейль"
    anti_repeat = ""
    if seen_titles:
        anti_repeat = f"\nВАЖНО: Пользователь уже готовил: {', '.join(seen_titles[-10:])}. Предложи АБСОЛЮТНО ДРУГОЙ коктейль!"

    prompt = (
        f"Ты профессиональный шеф-бармен и миксолог. Создай {alcol_type}.\n"
        f"Домашний бар пользователя / ингредиенты: '{bar_stock if bar_stock else 'джин, тоник, лимон, лед, мята'}'.\n"
        f"Атмосфера / повод: {vibe}.{anti_repeat}\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "title": "🍸 Изумрудный Джин-Тоник с мятой и огурцом",\n'
        '  "category": "Лонгдринк / Освежающий",\n'
        '  "strength": "Средняя (~12% ABV)",\n'
        '  "glassware": "Хайбол или бокал рокс с большим куском льда",\n'
        '  "ingredients": [\n'
        '    "Джин — 50 мл",\n'
        '    "Тоник индиан — 120 мл",\n'
        '    "Слайс свежего огурца — 2 шт",\n'
        '    "Веточка мяты и долька лайма",\n'
        '    "Крупный лед"\n'
        '  ],\n'
        '  "recipe_steps": [\n'
        '    "1. Наполните бокал кусковым льдом доверху.",\n'
        '    "2. Налейте 50 мл джина.",\n'
        '    "3. Аккуратно добавьте тоник по барной ложке.",\n'
        '    "4. Украсьте слайсом огурца и слегка хлопнутой веточкой мяты."\n'
        '  ],\n'
        '  "barman_secret": "💡 Хлопните мяту между ладонями перед подачей — это высвободит эфирные масла и подарит яркий аромат!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing cocktail JSON: {e}")

    return {
        "title": "🍸 Классический Джин-Тоник",
        "category": "Освежающий лонг",
        "strength": "12%",
        "glassware": "Хайбол со льдом",
        "ingredients": ["Джин 50мл", "Тоник 150мл", "Лайм", "Лед"],
        "recipe_steps": ["Наполнить бокал льдом", "Влить джин и тоник", "Украсить лаймом"],
        "barman_secret": "Используйте качественный кусковой лед."
    }
