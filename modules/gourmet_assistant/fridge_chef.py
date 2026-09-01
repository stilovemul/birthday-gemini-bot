import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("FridgeChef")


async def cook_from_fridge(user_id: int, ingredients_text: str = "", image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    ing_str = ingredients_text if ingredients_text else "яйца, сыр, остатки запеченной курицы, помидор, банка фасоли, соевый соус"
    prompt = (
        "Ты звездный шеф-повар. Твоя задача — спасти пользователя от голода и приготовить шедевр из того, что есть в холодильнике.\n"
        f"Список продуктов у пользователя: '{ing_str}'\n\n"
        "Предложи 3 отличных варианта блюд от самого быстрого до более сытного.\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "fridge_summary": "Из ваших ингредиентов можно приготовить отличные блюда без похода в магазин!",\n'
        '  "recipes": [\n'
        '    {\n'
        '      "name": "🍳 Опция 1: Фриттата по-домашнему за 10 мин",\n'
        '      "time": "10 минут",\n'
        '      "calories": 390,\n'
        '      "used_ingredients": ["яйца", "сыр", "курица", "помидор"],\n'
        '      "instructions": "Взбейте яйца, нарежьте курицу и томат, залейте на сковороду и посыпьте сыром под крышкой 6 минут."\n'
        '    },\n'
        '    {\n'
        '      "name": "🥗 Опция 2: Теплый боул с курицей и фасолью",\n'
        '      "time": "12 минут",\n'
        '      "calories": 440,\n'
        '      "used_ingredients": ["курица", "фасоль", "томат", "соевый соус"],\n'
        '      "instructions": "Прогрейте фасоль с курочкой на сковороде с ложкой соевого соуса, добавьте свежий томат и зелень."\n'
        '    },\n'
        '    {\n'
        '      "name": "🧀 Опция 3: Запеканка-минутница с сырной корочкой",\n'
        '      "time": "15 минут",\n'
        '      "calories": 480,\n'
        '      "used_ingredients": ["все ингредиенты"],\n'
        '      "instructions": "Смешайте ингредиенты в форме для запекания или сковороде, запеките до золотистой корочки сыра."\n'
        '    }\n'
        '  ],\n'
        '  "pro_tip": "💡 Не бойтесь сочетать овощи и белковые остатки — специи и правильный нагрев творят чудеса!"\n'
        "}"
    )

    if image_bytes:
        prompt_vision = "Определи все продукты на этом фото из холодильника и составь 3 рецепта блюд в формате JSON с полями fridge_summary, recipes (name, time, calories, used_ingredients, instructions), pro_tip."
        resp = await ask_gemini(user_id, prompt_vision, image_bytes=image_bytes)
    else:
        resp = await ask_gemini(user_id, prompt)

    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing fridge chef JSON: {e}")

    return {
        "fridge_summary": "Отличный набор продуктов для сытного обеда или ужина!",
        "recipes": [
            {
                "name": "🍳 Сковорода-микс из остатков продуктов",
                "time": "10 минут",
                "calories": 400,
                "used_ingredients": ["доступные продукты"],
                "instructions": "Быстро обжарьте все ингредиенты на сковороде, добавьте яйцо или сыр для связки."
            }
        ],
        "pro_tip": "Добавьте каплю соевого соуса или чеснока для насыщенного вкуса умами!"
    }
