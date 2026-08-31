import re
import json
import logging
from typing import Dict, Any, List
from core.gemini import ask_gemini

logger = logging.getLogger("BreakfastGenerator")


async def generate_express_breakfast(user_id: int, ingredients: str = "", mood: str = "энергичный", target_calories: int = 450) -> Dict[str, Any]:
    """
    Generates a 10-minute breakfast recipe with precise KBJU and step-by-step instructions.
    """
    prompt = (
        f"Ты шеф-повар и нутрициолог. Создай быстрый, сытный и вкусный завтрак за 10 минут.\n"
        f"Ингредиенты у пользователя: '{ingredients if ingredients else 'любые базовые продукты (яйца, овсянка, сыр, хлеб, творог, овощи)'}'.\n"
        f"Настроение/стиль: {mood}. Целевая калорийность: около {target_calories} ккал.\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "title": "🍳 Пышный омлет с томатами и сыром сулугуни",\n'
        '  "prep_time": "10 минут",\n'
        '  "calories": 420,\n'
        '  "protein": 24,\n'
        '  "fats": 22,\n'
        '  "carbs": 18,\n'
        '  "ingredients": ["3 яйца C1", "50г сыра", "1 томат", "1 ломтик цельнозернового хлеба", "зелень, соль, перец"],\n'
        '  "steps": [\n'
        '    "1. Взбейте яйца вилкой с щепоткой соли и 2 ст. ложками воды.",\n'
        '    "2. Нарежьте томат кубиками и слегка припустите на сковороде 1 минуту.",\n'
        '    "3. Залейте яйцами, посыпьте тертым сыром и томите под крышкой 4 минуты на среднем огне."\n'
        '  ],\n'
        '  "chef_tip": "💡 Подавайте с хрустящим тостом и чашкой свежезаваренного кофе для бодрого утра!"\n'
        "}"
    )
    
    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing breakfast JSON: {e}")

    return {
        "title": "🍳 Быстрый белковый омлет",
        "prep_time": "8 минут",
        "calories": 380,
        "protein": 22,
        "fats": 18,
        "carbs": 12,
        "ingredients": ["3 яйца", "сыр 40г", "зелень", "тост"],
        "steps": ["Взбейте яйца", "Обжарьте 4 минуты под крышкой", "Посыпьте сыром и зеленью"],
        "chef_tip": "Идеально с черным кофе!"
    }
