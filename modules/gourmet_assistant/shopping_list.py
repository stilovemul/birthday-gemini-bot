import html
import re
from typing import Dict, Any, List


def format_grocery_item(item: str) -> str:
    """Formats a single ingredient item as a checklist item."""
    clean = item.strip().lstrip("•-*0123456789. ")
    return f"▫️ [ ] <b>{html.escape(clean)}</b>"


def generate_shopping_list_text(recipe_data: Dict[str, Any]) -> str:
    """
    Constructs an interactive and copy-paste friendly supermarket grocery checklist
    from recipe ingredients or weekly meal plan shopping list.
    """
    title = recipe_data.get("title") or recipe_data.get("steak_title") or recipe_data.get("beer_name") or recipe_data.get("drink_name") or recipe_data.get("plan_title") or "Блюдо"
    title_clean = html.escape(str(title))

    lines = [
        f"🛒 <b>СПИСОК ПОКУПОК В МАГАЗИН:</b>",
        f"🍽 <i>{title_clean}</i>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    # Check if it's weekly meal plan with structured shopping list
    shop_dict = recipe_data.get("shopping_list")
    if isinstance(shop_dict, dict) and shop_dict:
        for cat, items in shop_dict.items():
            lines.append(f"\n<b>{html.escape(str(cat))}:</b>")
            if isinstance(items, list):
                for it in items:
                    lines.append(format_grocery_item(str(it)))
            elif isinstance(items, str):
                lines.append(format_grocery_item(items))
        
        lines.extend([
            "\n━━━━━━━━━━━━━━━━━━━",
            "💡 <b>Лайфхак:</b> Скопируйте этот список или перешлите себе в Избранное перед походом в супермаркет!",
            "🏪 <i>Цены актуальны для ВкусВилл / Перекресток / Самокат / Лента.</i>"
        ])
        return "\n".join(lines)

    # Standard recipe with ingredients list
    ingredients = recipe_data.get("ingredients") or recipe_data.get("proportions") or []
    if isinstance(ingredients, list) and ingredients:
        lines.append("\n📋 <b>Необходимые продукты:</b>")
        for ing in ingredients:
            lines.append(format_grocery_item(str(ing)))
    elif recipe_data.get("snacks"):
        # For craft beer / alcohol
        snacks = recipe_data.get("snacks")
        lines.append("\n🍟 <b>Рекомендованные закуски:</b>")
        if isinstance(snacks, dict):
            for k, v in snacks.items():
                if v:
                    lines.append(f"▫️ [ ] <b>{html.escape(str(v))}</b>")
        elif isinstance(snacks, list):
            for s in snacks:
                lines.append(format_grocery_item(str(s)))
    elif recipe_data.get("pairings"):
        pairings = recipe_data.get("pairings")
        lines.append("\n🧀 <b>Гастрономическая корзина к напитку:</b>")
        if isinstance(pairings, dict):
            for k, v in pairings.items():
                if v:
                    lines.append(f"▫️ [ ] <b>{html.escape(str(v))}</b>")
    else:
        # Fallback
        lines.append("\n▫️ [ ] <i>Базовые продукты для блюда (мясо/рыба, масло, специи, овощи)</i>")

    lines.extend([
        "\n━━━━━━━━━━━━━━━━━━━",
        "💡 <b>Удобно:</b> Нажимайте на чекбоксы в списке покупок или скопируйте текст сообщения!",
        "🛒 <i>Все ингредиенты легко найти в ближайшем магазине у дома.</i>"
    ])

    return "\n".join(lines)
