import re
import json
import logging
from typing import Dict, Any, List, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("RestaurantSauces")


async def get_restaurant_sauce(
    user_id: int,
    sauce_name: str = "",
    seen_titles: Optional[List[str]] = None
) -> Dict[str, Any]:
    s_name = sauce_name if sauce_name else "Зеленый Песто по-генуэзски / Аргентинский Чимичурри к мясу"
    anti_repeat = ""
    if seen_titles:
        anti_repeat = f"\nВАЖНО: Пользователь уже смотрел: {', '.join(seen_titles[-10:])}. Предложи АБСОЛЮТНО ДРУГОЙ ресторанный соус!"

    prompt = (
        "Ты соусье и шеф мишленовского уровня. Создай точный рецепт соуса ресторанного качества.\n"
        f"Запрос соуса: '{s_name}'.{anti_repeat}\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "title": "🌿 Аутентичный соус Чимичурри (Аргентина)",\n'
        '  "pairing": "Идеально к стейкам, шашлыку, запеченным овощам и птице",\n'
        '  "prep_time": "7 минут",\n'
        '  "shelf_life": "До 2 недель в холодильнике в стеклянной банке",\n'
        '  "ingredients": [\n'
        '    "Свежая петрушка и кинза — 1 крупный пучок",\n'
        '    "Чеснок — 4 зубчика (мелко порубить ножом)",\n'
        '    "Оливковое масло Extra Virgin — 100 мл",\n'
        '    "Красный винный уксус или сок лайма — 2 ст. ложки",\n'
        '    "Хлопья чили, орегано, морская соль, черничный/черный перец"\n'
        '  ],\n'
        '  "steps": [\n'
        '    "1. Зелень мелко порубите ножом (не блендером, чтобы сохранить текстуру).",\n'
        '    "2. Смешайте чеснок, специи, соль и винный уксус, дайте постоять 2 минуты.",\n'
        '    "3. Влейте оливковое масло, перемешайте и дайте настояться минимум 30 минут перед подачей."\n'
        '  ],\n'
        '  "sauce_secret": "💡 Ручная нарезка зелени не дает маслу горчить, а уксус раскрывает травяной букет!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing sauce JSON: {e}")

    return {
        "title": "🌿 Соус Чимичурри к мясу",
        "pairing": "К стейкам и шашлыку",
        "prep_time": "7 минут",
        "shelf_life": "2 недели в холоде",
        "ingredients": ["Петрушка 1 пучок", "Чеснок 4 зубчика", "Оливковое масло 100мл", "Винный уксус 2 ст.л.", "Чили, орегано, соль"],
        "steps": ["Мелко порубить зелень и чеснок", "Смешать со специями и уксусом", "Влить оливковое масло и настоять 30 мин"],
        "sauce_secret": "Рубите зелень ножом, а не блендером!"
    }
