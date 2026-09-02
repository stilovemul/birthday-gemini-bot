import io
import re
import html
import logging
from typing import Dict, Any, Optional, List

from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.voice_assistant.transcriber import transcribe_audio_gemini
from modules.gourmet_assistant.storage import (
    add_seen_recipe,
    get_seen_recipes,
    set_user_last_gourmet,
    get_user_last_gourmet
)
from modules.gourmet_assistant.shopping_list import generate_shopping_list_text
from modules.gourmet_assistant.curated_catalog import CURATED_PRESETS, get_preset_by_id
from modules.gourmet_assistant.keyboards import (
    get_gourmet_main_keyboard,
    get_category_presets_keyboard,
    get_gourmet_result_keyboard
)

from modules.gourmet_assistant.breakfast import generate_express_breakfast
from modules.gourmet_assistant.barman import craft_cocktail
from modules.gourmet_assistant.fastfood_healthy import generate_healthy_fastfood
from modules.gourmet_assistant.fridge_chef import cook_from_fridge
from modules.gourmet_assistant.steak_master import get_steak_guide
from modules.gourmet_assistant.express_meals import generate_15min_meal
from modules.gourmet_assistant.weekly_meal_plan import generate_weekly_meal_plan
from modules.gourmet_assistant.shashlik_calc import calculate_shashlik_marinade
from modules.gourmet_assistant.sauces import get_restaurant_sauce
from modules.gourmet_assistant.asian_cuisine import get_asian_dish_recipe
from modules.gourmet_assistant.craft_beer import get_craft_beer_guide
from modules.gourmet_assistant.wine_spirits import get_wine_spirits_guide
from modules.gourmet_assistant.shelf_advisor import analyze_alcohol_shelf, format_shelf_advisor_message

logger = logging.getLogger("GourmetHandlers")
router = Router(name="gourmet_assistant")


# --- TEXT FORMATTERS ---

def translate_flavor_notes(text: str) -> str:
    if not text:
        return "Солодовые и хмелевые ноты"
    t = str(text)
    mapping = {
        "citrus": "цитрусы", "pine": "хвоя", "resin": "хвойная смола",
        "tropical": "тропические фрукты", "grapefruit": "грейпфрут", "mango": "манго",
        "passionfruit": "маракуйя", "peach": "персик", "hops": "хмель", "hoppy": "хмелевой",
        "malt": "солод", "malty": "солодовый", "caramel": "карамель", "coffee": "кофе",
        "chocolate": "шоколад", "vanilla": "ваниль", "oak": "дуб", "smoke": "копченые ноты",
        "berries": "лесные ягоды", "cherry": "вишня", "banana": "банан", "clove": "гвоздика",
        "coriander": "кориандр", "orange peel": "цедра апельсина", "lemon": "лимон",
        "lime": "лайм", "herbal": "пряные травы", "floral": "цветочные ноты",
        "spicy": "пряности", "crisp": "хрустящий освежающий", "roasted": "обжаренный солод",
        "toffee": "ириска", "biscuit": "бисквит", "honey": "мед"
    }
    for eng, rus in mapping.items():
        t = re.sub(r'\b' + re.escape(eng) + r'\b', rus, t, flags=re.IGNORECASE)
    return t


def format_breakfast_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'Экспресс-завтрак')))
    prep = html.escape(str(data.get('prep_time', '10 мин')))
    cal = data.get('calories', 400)
    prot = data.get('protein', 20)
    fats = data.get('fats', 15)
    carbs = data.get('carbs', 25)

    lines = [
        f"🍳 <b>{title}</b>",
        f"⏱ Время: <b>{prep}</b> | ⚡️ КБЖУ: <b>{cal} ккал</b> (Б: {prot}г | Ж: {fats}г | У: {carbs}г)\n",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {html.escape(str(ing))}")
    lines.append("\n👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("chef_tip"):
        lines.append(f"\n{html.escape(str(data['chef_tip']))}")
    lines.append("\n<i>💡 Голосом или текстом назовите любые продукты — шеф придумает новый завтрак!</i>")
    return "\n".join(lines)


def format_fastfood_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'ПП-Фастфуд')))
    prep = html.escape(str(data.get('prep_time', '15 мин')))
    cal = data.get('calories', 400)
    prot = data.get('protein', 30)
    fats = data.get('fats', 12)
    carbs = data.get('carbs', 40)
    comp = html.escape(str(data.get('fastfood_comparison', 'В 2 раза меньше калорий!')))

    lines = [
        f"🌯 <b>{title}</b>",
        f"⏱ Время: <b>{prep}</b> | ⚡️ КБЖУ: <b>{cal} ккал</b> (Б: {prot}г | Ж: {fats}г | У: {carbs}г)",
        f"🔥 <i>{comp}</i>\n",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {html.escape(str(ing))}")
    lines.append("\n👨‍🍳 <b>Технология приготовления:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("chef_secret"):
        lines.append(f"\n{html.escape(str(data['chef_secret']))}")
    lines.append("\n<i>💡 Напишите любой фастфуд (бургер, шаверма, пицца, наггетсы), чтобы сделать его полезным!</i>")
    return "\n".join(lines)


def format_fridge_message(data: dict) -> str:
    summary = html.escape(str(data.get('fridge_summary', 'Вот 3 варианта блюд:')))
    lines = [
        "🧊 <b>Шеф по холодильнику — Готовим из того, что есть:</b>",
        f"💬 <i>{summary}</i>\n"
    ]
    for i, r in enumerate(data.get("recipes", []), 1):
        name = html.escape(str(r.get('name', f'Рецепт {i}')))
        time_str = html.escape(str(r.get('time', '10 мин')))
        cal = r.get('calories', 400)
        used_list = r.get('used_ingredients', [])
        used = html.escape(', '.join(str(x) for x in used_list)) if isinstance(used_list, list) else html.escape(str(used_list))
        inst = html.escape(str(r.get('instructions', '')))

        lines.append(f"<b>{name}</b>")
        lines.append(f"⏱ <b>{time_str}</b> | ⚡️ <b>{cal} ккал</b>")
        lines.append(f"🛒 Продукты: <i>{used}</i>")
        lines.append(f"📝 {inst}\n")

    if data.get("pro_tip"):
        lines.append(html.escape(str(data['pro_tip'])))
    lines.append("\n<i>💡 Пришлите ФОТО открытого холодильника или список продуктов — шеф составит меню!</i>")
    return "\n".join(lines)


def format_steak_message(data: dict) -> str:
    title = html.escape(str(data.get('steak_title', 'Стейк')))
    core_temp = html.escape(str(data.get('target_core_temp', '54-56°C')))
    crust = html.escape(str(data.get('crust_sear_time', 'По 2 мин с каждой стороны')))
    basting = html.escape(str(data.get('basting_time', '1-1.5 мин')))
    rest = html.escape(str(data.get('rest_time', '5 минут под фольгой')))

    lines = [
        f"🥩 <b>{title}</b>",
        f"🌡 Целевая температура внутри: <b>{core_temp}</b>",
        f"⏱ Обжарка корочки: <b>{crust}</b>",
        f"🧈 Бастинг (масло + травы): <b>{basting}</b>",
        f"⏳ Отдых мяса: <b>{rest}</b>\n",
        "👨‍🍳 <b>Пошаговая инструкция шефа:</b>"
    ]
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("chef_rule"):
        lines.append(f"\n{html.escape(str(data['chef_rule']))}")
    lines.append("\n<i>💡 Назовите отруб, толщину или пришлите ФОТО мяса — шеф рассчитает точный тайминг!</i>")
    return "\n".join(lines)


def format_express_meal_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'Блюдо за 15 минут')))
    prep = html.escape(str(data.get('prep_time', '15 минут')))
    utensils = html.escape(str(data.get('utensils', '1 сковорода')))
    cal = data.get('calories', 500)
    prot = data.get('protein', 35)
    fats = data.get('fats', 15)
    carbs = data.get('carbs', 50)

    lines = [
        f"⚡️ <b>{title}</b>",
        f"⏱ Время: <b>{prep}</b> | 🍳 Посуда: <b>{utensils}</b>",
        f"⚡️ КБЖУ: <b>{cal} ккал</b> (Б: {prot}г | Ж: {fats}г | У: {carbs}г)\n",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {html.escape(str(ing))}")
    lines.append("\n👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("express_hack"):
        lines.append(f"\n{html.escape(str(data['express_hack']))}")
    lines.append("\n<i>💡 Напишите любое пожелание («из рыбы», «паста с индейкой», «вок за 10 мин») для нового рецепта!</i>")
    return "\n".join(lines)


def format_meal_plan_message(data: dict) -> str:
    title = html.escape(str(data.get('plan_title', 'Недельный рацион ПП')))
    lines = [f"📅 <b>{title}</b>\n"]
    for d in data.get("days", []):
        day_str = html.escape(str(d.get('day', 'День')))
        bf = html.escape(str(d.get('breakfast', '')))
        lu = html.escape(str(d.get('lunch', '')))
        di = html.escape(str(d.get('dinner', '')))
        lines.append(f"🗓 <b>{day_str}:</b>")
        lines.append(f"   🌅 Завтрак: {bf}")
        lines.append(f"   ☀️ Обед: {lu}")
        lines.append(f"   🌙 Ужин: {di}\n")

    lines.append("🛒 <b>АВТОМАТИЧЕСКИЙ СПИСОК ПОКУПОК НА НЕДЕЛЮ:</b>")
    shop = data.get("shopping_list", {})
    if isinstance(shop, dict):
        for cat, items in shop.items():
            lines.append(f"<b>{html.escape(str(cat))}:</b>")
            if isinstance(items, list):
                for it in items:
                    lines.append(f"   ▫️ {html.escape(str(it))}")
            elif isinstance(items, str):
                lines.append(f"   ▫️ {html.escape(items)}")
    if data.get("mealprep_tip"):
        lines.append(f"\n{html.escape(str(data['mealprep_tip']))}")
    lines.append("\n<i>💡 Нажмите «🛒 Список покупок в магазин» ниже для удобного чек-листа в супермаркете!</i>")
    return "\n".join(lines)


def format_shashlik_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'Маринад для шашлыка')))
    m_time = html.escape(str(data.get('marinade_time', '4-6 часов')))
    coals = html.escape(str(data.get('coals_needed', '1 мешок (2.5-3 кг)')))

    lines = [
        f"🍢 <b>{title}</b>",
        f"⏳ Время маринования: <b>{m_time}</b>",
        f"🔥 Расход углей: <b>{coals}</b>\n",
        "⚖️ <b>Точные пропорции ингредиентов:</b>"
    ]
    for prop in data.get("proportions", []):
        lines.append(f"  • {html.escape(str(prop))}")
    lines.append("\n👨‍🍳 <b>Технология маринования и жарки:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("grill_secrets"):
        lines.append(f"\n{html.escape(str(data['grill_secrets']))}")
    lines.append("\n<i>💡 Укажите вес мяса или пожелания к маринаду (например: «3 кг индейки», «баранина с гранатом»)!</i>")
    return "\n".join(lines)


def format_sauce_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'Соус шеф-повара')))
    pairing = html.escape(str(data.get('pairing', 'Ко всем блюдам')))
    prep = html.escape(str(data.get('prep_time', '7 мин')))
    shelf = html.escape(str(data.get('shelf_life', '2 недели')))

    lines = [
        f"🥫 <b>{title}</b>",
        f"🍽 Сочетаемость: <i>{pairing}</i>",
        f"⏱ Время: <b>{prep}</b> | ❄️ Хранение: <b>{shelf}</b>\n",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {html.escape(str(ing))}")
    lines.append("\n👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("sauce_secret"):
        lines.append(f"\n{html.escape(str(data['sauce_secret']))}")
    lines.append("\n<i>💡 Назовите любой соус (песто, голландез, барбекю, цезарь, терияки) для пошагового рецепта!</i>")
    return "\n".join(lines)


def format_asian_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'Азиатское блюдо')))
    country = html.escape(str(data.get('country', 'Азия')))
    spiciness = html.escape(str(data.get('spiciness', 'Средняя')))
    prep = html.escape(str(data.get('prep_time', '25 мин')))
    cal = data.get('calories', 500)

    lines = [
        f"🍜 <b>{title}</b>",
        f"🌏 Страна: <b>{country}</b> | 🌶 Острота: <b>{spiciness}</b>",
        f"⏱ Время: <b>{prep}</b> | ⚡️ КБЖУ: <b>{cal} ккал</b>\n",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {html.escape(str(ing))}")
    lines.append("\n👨‍🍳 <b>Пошаговый вок-рецепт:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("asian_secret"):
        lines.append(f"\n{html.escape(str(data['asian_secret']))}")
    lines.append("\n<i>💡 Напишите любое азиатское блюдо (Том Ям, Пад Тай, Рамен, Карри, Кимчи) для рецепта!</i>")
    return "\n".join(lines)


def format_craft_beer_message(data: dict) -> str:
    fn = data.get("flavor_notes", "")
    if isinstance(fn, list):
        fn_str = ", ".join(str(x) for x in fn)
    else:
        fn_str = str(fn) if fn else "Солодовые и хмелевые ноты"
    fn_str = translate_flavor_notes(fn_str)

    b_name = html.escape(str(data.get('beer_name', 'Крафтовое пиво')))
    brewery = html.escape(str(data.get('brewery', 'Крафтовая')))
    style = html.escape(str(data.get('style', 'Ale')))
    abv = html.escape(str(data.get('abv', '5.0%')))
    ibu = html.escape(str(data.get('ibu', '20 IBU')))
    untappd = html.escape(str(data.get('untappd_rating', '4.0/5')))
    taste = html.escape(str(data.get('taste_verdict', '')))
    buy = html.escape(str(data.get('buy_verdict', '')))
    temp = html.escape(str(data.get('serving_temp', '6-8°C')))

    lines = [
        f"🍺 <b>{b_name}</b>",
        f"🏭 Пивоварня: <b>{brewery}</b> | Стиль: <i>{style}</i>",
        f"📊 Крепость: <b>{abv}</b> | Горечь: <b>{ibu}</b> | ⭐️ <b>Untappd: {untappd}</b>\n",
        f"👅 <b>Вкусное или нет? (Консенсус отзывов):</b>\n{taste}\n",
        f"🛒 <b>Вердикт сомелье:</b>\n{buy}\n",
        "🍟 <b>ИДЕАЛЬНЫЕ ЗАКУСКИ (FOOD PAIRING):</b>"
    ]
    snacks = data.get("snacks", {})
    snack_lines = []
    if isinstance(snacks, dict):
        croutons = snacks.get("croutons") or snacks.get("crouton") or snacks.get("сухарики") or snacks.get("гренки")
        fish = snacks.get("fish") or snacks.get("seafood") or snacks.get("рыба") or snacks.get("морепродукты")
        chips = snacks.get("chips") or snacks.get("crisps") or snacks.get("чипсы") or snacks.get("снеки")
        hot_food = snacks.get("hot_food") or snacks.get("hot") or snacks.get("сыр") or snacks.get("горячее")

        if croutons:
            snack_lines.append(f"  🍞 <b>Сухарики/гренки:</b> <i>{html.escape(str(croutons))}</i>")
        if fish:
            snack_lines.append(f"  🐟 <b>Рыбка/морепродукты:</b> <i>{html.escape(str(fish))}</i>")
        if chips:
            snack_lines.append(f"  🥔 <b>Чипсы/снеки:</b> <i>{html.escape(str(chips))}</i>")
        if hot_food:
            snack_lines.append(f"  🍔 <b>Горячее/сыры:</b> <i>{html.escape(str(hot_food))}</i>")

        if not snack_lines:
            for k, v in snacks.items():
                if v:
                    snack_lines.append(f"  • <b>{html.escape(k.replace('_', ' ').capitalize())}:</b> <i>{html.escape(str(v))}</i>")
    elif isinstance(snacks, list):
        for s in snacks:
            if s:
                snack_lines.append(f"  • <i>{html.escape(str(s))}</i>")

    if not snack_lines:
        snack_lines = [
            "  🍞 <b>Сухарики/гренки:</b> <i>Чесночные бородинские гренки</i>",
            "  🐟 <b>Рыбка/морепродукты:</b> <i>Вяленый лосось или кальмары</i>",
            "  🍔 <b>Горячее/сыры:</b> <i>Сочный бургер, сыр Чеддер</i>"
        ]
    lines.extend(snack_lines)

    hang = data.get("hangover_risk", {})
    if isinstance(hang, dict) and hang:
        r_lvl = html.escape(str(hang.get('risk_level', 'Низкий')))
        m_fore = html.escape(str(hang.get('morning_forecast', '')))
        lines.append("\n🤕 <b>БУДЕТ ЛИ УТРОМ БОЛЕТЬ ГОЛОВА? (Похмельный фактор):</b>")
        lines.append(f"  • Риск: <b>{r_lvl}</b>")
        lines.append(f"  • Прогноз: <i>{m_fore}</i>")
        if hang.get("hangover_cure"):
            lines.append(f"  • {html.escape(str(hang['hangover_cure']))}")

    lines.append(f"\n🌿 Вкусовые ноты: <i>{html.escape(fn_str)}</i> | ❄️ Подача: <b>{temp}</b>")
    lines.append("\n<i>💡 Пришлите ФОТО банки/этикетки пива или напишите сорт для разбора сомелье!</i>")
    return "\n".join(lines)


def format_cocktail_message(data: dict) -> str:
    title = html.escape(str(data.get('title', 'Коктейль')))
    cat = html.escape(str(data.get('category', 'Классика')))
    strg = html.escape(str(data.get('strength', '12%')))
    glass = html.escape(str(data.get('glassware', 'Хайбол со льдом')))

    lines = [
        f"🍸 <b>{title}</b>",
        f"🏷 Стиль: <i>{cat}</i> | Крепость: <b>{strg}</b>",
        f"🥃 Бокал: <i>{glass}</i>\n",
        "🧊 <b>Состав и пропорции:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {html.escape(str(ing))}")
    lines.append("\n🍹 <b>Метод приготовления:</b>")
    for step in data.get("recipe_steps", []):
        lines.append(f"  {html.escape(str(step))}")
    if data.get("barman_secret"):
        lines.append(f"\n{html.escape(str(data['barman_secret']))}")
    lines.append("\n<i>💡 Перечислите ваши напитки дома или напишите «безалкогольный» для моктейля!</i>")
    return "\n".join(lines)


def format_wine_spirits_message(data: dict) -> str:
    notes = data.get("tasting_notes", "")
    if isinstance(notes, list):
        notes_str = ", ".join(str(x) for x in notes)
    else:
        notes_str = str(notes) if notes else "Благородный сбалансированный букет"
    notes_str = translate_flavor_notes(notes_str)

    d_name = html.escape(str(data.get('drink_name', 'Алкогольный напиток')))
    prod = html.escape(str(data.get('producer', 'Мастер')))
    cat = html.escape(str(data.get('category', 'Премиум')))
    origin = html.escape(str(data.get('origin', 'Мир')))
    abv = html.escape(str(data.get('abv', '40%')))
    rating = html.escape(str(data.get('rating', '4.2 / 5.0')))
    taste = html.escape(str(data.get('taste_verdict', '')))
    buy = html.escape(str(data.get('buy_verdict', '')))
    serving = html.escape(str(data.get('serving', 'Комнатная / Охлажденным')))

    lines = [
        f"🍷 <b>{d_name}</b>",
        f"🏭 Производитель: <b>{prod}</b> | Категория: <i>{cat}</i>",
        f"🌍 Регион: <i>{origin}</i> | Крепость: <b>{abv}</b> | ⭐️ <b>Рейтинг: {rating}</b>\n",
        f"👅 <b>Вкус и мягкость (Консенсус отзывов):</b>\n{taste}\n",
        f"🛒 <b>Вердикт сомелье:</b>\n{buy}\n",
        "🧀 <b>ИДЕАЛЬНЫЕ ГАСТРОНОМИЧЕСКИЕ ПАРЫ:</b>"
    ]
    pairings = data.get("pairings", {})
    pairing_lines = []
    if isinstance(pairings, dict):
        cheeses_meats = pairings.get("cheeses_meats") or pairings.get("cheese") or pairings.get("meat")
        hot_dishes = pairings.get("hot_dishes") or pairings.get("hot") or pairings.get("main_dishes")
        traditional = pairings.get("traditional_snacks") or pairings.get("snacks") or pairings.get("traditional")
        fruits = pairings.get("fruits_desserts") or pairings.get("desserts") or pairings.get("fruits")

        if cheeses_meats:
            pairing_lines.append(f"  🧀 <b>Сыры/Мясные деликатесы:</b> <i>{html.escape(str(cheeses_meats))}</i>")
        if hot_dishes:
            pairing_lines.append(f"  🥩 <b>Горячие блюда:</b> <i>{html.escape(str(hot_dishes))}</i>")
        if traditional:
            pairing_lines.append(f"  🍋 <b>Закуски под крепкое:</b> <i>{html.escape(str(traditional))}</i>")
        if fruits:
            pairing_lines.append(f"  🥖 <b>Десерты/Фрукты:</b> <i>{html.escape(str(fruits))}</i>")

        if not pairing_lines:
            for k, v in pairings.items():
                if v:
                    pairing_lines.append(f"  • <b>{html.escape(k.replace('_', ' ').capitalize())}:</b> <i>{html.escape(str(v))}</i>")
    elif isinstance(pairings, list):
        for p in pairings:
            if p:
                pairing_lines.append(f"  • <i>{html.escape(str(p))}</i>")

    if not pairing_lines:
        pairing_lines = [
            "  🧀 <b>Сыры/Деликатесы:</b> <i>Пармезан, прошутто, вяленое мясо</i>",
            "  🥩 <b>Горячее:</b> <i>Стейк из говядины или утка</i>"
        ]
    lines.extend(pairing_lines)

    hang = data.get("hangover_risk", {})
    if isinstance(hang, dict) and hang:
        r_lvl = html.escape(str(hang.get('risk_level', 'Умеренный')))
        m_fore = html.escape(str(hang.get('morning_forecast', '')))
        lines.append("\n🤕 <b>БУДЕТ ЛИ УТРОМ БОЛЕТЬ ГОЛОВА? (Похмельный фактор):</b>")
        lines.append(f"  • Риск: <b>{r_lvl}</b>")
        lines.append(f"  • Прогноз: <i>{m_fore}</i>")
        if hang.get("safety_rule"):
            lines.append(f"  • {html.escape(str(hang['safety_rule']))}")

    lines.append(f"\n🌿 Букет: <i>{html.escape(notes_str)}</i> | ❄️ Подача: <b>{serving}</b>")
    lines.append("\n<i>💡 Пришлите ФОТО бутылки/этикетки (вино, виски, коньяк, водка) для мгновенного разбора!</i>")
    return "\n".join(lines)


# --- MAIN MENU ENTRY POINT ---

@router.message(Command("gourmet"))
@router.message(Command("breakfast"))
@router.message(Command("barman"))
@router.message(Command("food"))
@router.message(F.text.in_(["🍽 Еда", "🍳 Еда", "Еда", "еда", "🍳 Завтрак & 🍸 Бармен", "🍳 Экспресс-Завтраки", "🍸 AI-Бармен", "🍳 Кулинарный шеф", "🍽 Кулинария & Бар"]))
async def cmd_gourmet_menu(message: types.Message, state: FSMContext):
    await state.clear()
    intro_text = (
        "🍳 <b>Гранд-Шеф & 🍸 AI-Бармен — Персональный кулинарный центр:</b>\n\n"
        "Выберите направление:\n"
        "• <b>🍳 Завтраки & ⚡️ Блюда за 15 мин</b> — экспресс-кулинария для занятых людей.\n"
        "• <b>🌯 ПП-Фастфуд</b> — любимая шаверма, бургеры и пицца без вреда для фигуры.\n"
        "• <b>🧊 Шеф из холодильника</b> — рецепты по фото или списку остатков продуктов.\n"
        "• <b>🥩 Таймер стейков & 🍢 Маринад шашлыка</b> — мясная школа идеальной сочности.\n"
        "• <b>📅 Рацион на неделю + Список</b> — меню ПП и готовый список в супермаркет.\n"
        "• <b>🥫 Соусы шефов & 🍜 Азиатская кухня</b> — ресторанный уровень дома.\n"
        "• <b>🍸 AI-Бармен & 🍺 Крафтовое пиво</b> — гид по стилям и авторские миксы.\n"
        "• <b>🍷 Вино & Крепкое</b> — карманный сомелье с разбором рейтингов и закусок.\n\n"
        "👇 <i>Выберите раздел на кнопках ниже:</i>"
    )
    await message.answer(intro_text, parse_mode=ParseMode.HTML, reply_markup=get_gourmet_main_keyboard())


# --- CATEGORY ENTRY DISPATCHER ---

CATEGORY_STATE_MAP = {
    "breakfast": ActiveModeStates.breakfast_mode,
    "express": ActiveModeStates.express_meals_mode,
    "fastfood": ActiveModeStates.healthy_fastfood_mode,
    "fridge": ActiveModeStates.fridge_chef_mode,
    "steak": ActiveModeStates.steak_timer_mode,
    "shashlik": ActiveModeStates.shashlik_calc_mode,
    "mealplan": ActiveModeStates.weekly_meal_plan_mode,
    "sauces": ActiveModeStates.restaurant_sauces_mode,
    "asian": ActiveModeStates.asian_cuisine_mode,
    "beer": ActiveModeStates.craft_beer_mode,
    "wine_spirits": ActiveModeStates.wine_spirits_mode,
    "barman": ActiveModeStates.barman_mode
}

CATEGORY_TITLES = {
    "breakfast": "🍳 Завтрак за 10 мин",
    "express": "⚡️ Блюда за 15 мин",
    "fastfood": "🌯 ПП-Фастфуд",
    "fridge": "🧊 Шеф из холодильника",
    "steak": "🥩 Таймер стейков",
    "shashlik": "🍢 Маринад шашлыка",
    "mealplan": "📅 Меню на неделю + Список",
    "sauces": "🥫 Соусы шефов",
    "asian": "🍜 Азиатская кухня",
    "beer": "🍺 Пивной сомелье",
    "wine_spirits": "🍷 Вино, Водка, Коньяк & Алкоголь",
    "barman": "🍸 AI-Бармен & Коктейли"
}


@router.callback_query(F.data.startswith("gourmet_cat_"))
async def cb_gourmet_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.replace("gourmet_cat_", "")
    target_state = CATEGORY_STATE_MAP.get(cat, ActiveModeStates.breakfast_mode)
    await state.set_state(target_state)

    cat_title = CATEGORY_TITLES.get(cat, "Еда")
    set_user_last_gourmet(callback.from_user.id, cat, "")

    text = (
        f"<b>{cat_title}:</b>\n\n"
        "Выберите готовый пресет шеф-повара или напишите/надиктуйте голосом свои пожелания (продукты, калории, время):\n"
    )

    await callback.message.answer(
        f"👇 <b>{cat_title} — готовые пресеты:</b>",
        reply_markup=get_category_presets_keyboard(cat)
    )
    await callback.answer()


# Support legacy callbacks from older messages
@router.callback_query(F.data.startswith("mode_start_"))
async def cb_legacy_mode_start(callback: types.CallbackQuery, state: FSMContext):
    legacy_map = {
        "mode_start_breakfast": "breakfast",
        "mode_start_express": "express",
        "mode_start_fastfood": "fastfood",
        "mode_start_fridge": "fridge",
        "mode_start_steak": "steak",
        "mode_start_shashlik": "shashlik",
        "mode_start_mealplan": "mealplan",
        "mode_start_sauces": "sauces",
        "mode_start_asian": "asian",
        "mode_start_beer": "beer",
        "mode_start_wine_spirits": "wine_spirits",
        "mode_start_barman": "barman"
    }
    cat = legacy_map.get(callback.data, "breakfast")
    await cb_run_category_generator(callback, state, cat)


# --- PRESET HANDLERS ---

@router.callback_query(F.data.startswith("gourmet_pr_"))
async def cb_gourmet_preset(callback: types.CallbackQuery, state: FSMContext):
    pr_id = callback.data.replace("gourmet_pr_", "")
    preset = get_preset_by_id(pr_id)
    if not preset:
        await callback.answer("⚠️ Пресет не найден.")
        return

    cat = preset.get("category", "breakfast")
    target_state = CATEGORY_STATE_MAP.get(cat, ActiveModeStates.breakfast_mode)
    await state.set_state(target_state)

    user_id = callback.from_user.id
    seen = get_seen_recipes(user_id, cat)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer(f"👨‍🍳 Готовлю {preset.get('title', 'рецепт')}...")

    data = None
    formatted_text = ""

    if cat == "breakfast":
        data = await generate_express_breakfast(user_id, ingredients=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_breakfast_message(data)
    elif cat == "express":
        data = await generate_15min_meal(user_id, query=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_express_meal_message(data)
    elif cat == "fastfood":
        data = await generate_healthy_fastfood(user_id, dish_query=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_fastfood_message(data)
    elif cat == "fridge":
        data = await cook_from_fridge(user_id, ingredients_text=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_fridge_message(data)
    elif cat == "steak":
        data = await get_steak_guide(user_id, cut=preset.get("cut", "Рибай"), doneness=preset.get("doneness", "Medium Rare"), thickness_cm=preset.get("thickness", 2.5), seen_titles=seen)
        formatted_text = format_steak_message(data)
    elif cat == "shashlik":
        data = await calculate_shashlik_marinade(user_id, meat_type=preset.get("meat", "Свиная шея"), weight_kg=preset.get("weight", 2.0), style=preset.get("style", "луковый сок"), seen_titles=seen)
        formatted_text = format_shashlik_message(data)
    elif cat == "mealplan":
        data = await generate_weekly_meal_plan(user_id, goal=preset.get("goal", "баланс"), calorie_target=preset.get("cals", 2000), seen_titles=seen)
        formatted_text = format_meal_plan_message(data)
    elif cat == "sauces":
        data = await get_restaurant_sauce(user_id, sauce_name=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_sauce_message(data)
    elif cat == "asian":
        data = await get_asian_dish_recipe(user_id, dish_name=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_asian_message(data)
    elif cat == "beer":
        data = await get_craft_beer_guide(user_id, query=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_craft_beer_message(data)
    elif cat == "wine_spirits":
        data = await get_wine_spirits_guide(user_id, query=preset.get("query", ""), seen_titles=seen)
        formatted_text = format_wine_spirits_message(data)
    elif cat == "barman":
        data = await craft_cocktail(user_id, bar_stock=preset.get("stock", ""), non_alcoholic=preset.get("non_alc", False), seen_titles=seen)
        formatted_text = format_cocktail_message(data)

    if data:
        title = data.get("title") or data.get("steak_title") or data.get("beer_name") or data.get("drink_name") or data.get("plan_title") or preset.get("title", "")
        add_seen_recipe(user_id, cat, title, full_data=data)
        set_user_last_gourmet(user_id, cat, preset.get("query", "") or preset.get("title", ""), full_data=data)

    await callback.message.answer(
        formatted_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_gourmet_result_keyboard(cat, has_shoplist=(cat != "beer" and cat != "wine_spirits"))
    )


# --- MORE / ANOTHER RECIPE HANDLER ---

@router.callback_query(F.data.startswith("gourmet_more_"))
@router.callback_query(F.data.startswith("gourmet_rnd_"))
async def cb_gourmet_more(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data.replace("gourmet_more_", "").replace("gourmet_rnd_", "")
    await cb_run_category_generator(callback, state, cat, is_more=True)


async def cb_run_category_generator(callback: types.CallbackQuery, state: FSMContext, cat: str, is_more: bool = False):
    target_state = CATEGORY_STATE_MAP.get(cat, ActiveModeStates.breakfast_mode)
    await state.set_state(target_state)

    user_id = callback.from_user.id
    seen = get_seen_recipes(user_id, cat)
    last_info = get_user_last_gourmet(user_id)
    last_query = last_info.get("query", "") if last_info.get("category") == cat else ""

    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("🔄 Подбираю новый уникальный рецепт шефа...")

    data = None
    formatted_text = ""

    if cat == "breakfast":
        data = await generate_express_breakfast(user_id, ingredients=last_query, mood="разнообразный и аппетитный", seen_titles=seen)
        formatted_text = format_breakfast_message(data)
    elif cat == "express":
        data = await generate_15min_meal(user_id, query=last_query or "быстрый ресторанный ужин", seen_titles=seen)
        formatted_text = format_express_meal_message(data)
    elif cat == "fastfood":
        data = await generate_healthy_fastfood(user_id, dish_query=last_query or "полезный фастфуд", seen_titles=seen)
        formatted_text = format_fastfood_message(data)
    elif cat == "fridge":
        data = await cook_from_fridge(user_id, ingredients_text=last_query, seen_titles=seen)
        formatted_text = format_fridge_message(data)
    elif cat == "steak":
        data = await get_steak_guide(user_id, cut=last_query or "Рибай", doneness="Medium", seen_titles=seen)
        formatted_text = format_steak_message(data)
    elif cat == "shashlik":
        data = await calculate_shashlik_marinade(user_id, meat_type=last_query or "Свиная шея", weight_kg=2.0, seen_titles=seen)
        formatted_text = format_shashlik_message(data)
    elif cat == "mealplan":
        data = await generate_weekly_meal_plan(user_id, goal=last_query or "сбалансированное питание", seen_titles=seen)
        formatted_text = format_meal_plan_message(data)
    elif cat == "sauces":
        data = await get_restaurant_sauce(user_id, sauce_name=last_query or "ресторанный соус", seen_titles=seen)
        formatted_text = format_sauce_message(data)
    elif cat == "asian":
        data = await get_asian_dish_recipe(user_id, dish_name=last_query or "азиатское блюдо", seen_titles=seen)
        formatted_text = format_asian_message(data)
    elif cat == "beer":
        data = await get_craft_beer_guide(user_id, query=last_query or "топовый крафтовый сорт", seen_titles=seen)
        formatted_text = format_craft_beer_message(data)
    elif cat == "wine_spirits":
        data = await get_wine_spirits_guide(user_id, query=last_query or "благородный напиток", seen_titles=seen)
        formatted_text = format_wine_spirits_message(data)
    elif cat == "barman":
        data = await craft_cocktail(user_id, bar_stock=last_query or "джин, тоник, ром, сок, цитрусовые, лед", seen_titles=seen)
        formatted_text = format_cocktail_message(data)

    if data:
        title = data.get("title") or data.get("steak_title") or data.get("beer_name") or data.get("drink_name") or data.get("plan_title") or "Рецепт"
        add_seen_recipe(user_id, cat, title, full_data=data)
        set_user_last_gourmet(user_id, cat, last_query, full_data=data)

    await callback.message.answer(
        formatted_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_gourmet_result_keyboard(cat, has_shoplist=(cat != "beer" and cat != "wine_spirits"))
    )


# --- SHOPPING LIST HANDLER ---

@router.callback_query(F.data.startswith("gourmet_shoplist_"))
async def cb_gourmet_shoplist(callback: types.CallbackQuery):
    cat = callback.data.replace("gourmet_shoplist_", "")
    user_id = callback.from_user.id
    last_info = get_user_last_gourmet(user_id)
    last_recipe = last_info.get("last_recipe", {})

    if not last_recipe:
        await callback.answer("⚠️ Сначала сгенерируйте рецепт для составления списка покупок.", show_alert=True)
        return

    await callback.answer("🛒 Формирую чек-лист для супермаркета...")
    shop_text = generate_shopping_list_text(last_recipe)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другой рецепт", callback_data=f"gourmet_more_{cat}"),
                InlineKeyboardButton(text="🍽 Все категории", callback_data="gourmet_back_to_menu")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )

    await callback.message.answer(shop_text, parse_mode=ParseMode.HTML, reply_markup=kb)


# --- NAVIGATION HANDLERS ---

@router.callback_query(F.data == "gourmet_back_to_menu")
async def cb_gourmet_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    intro_text = (
        "🍳 <b>Персональный кулинарный центр:</b>\n"
        "Выберите направление кулинарии на кнопках ниже:"
    )
    await callback.message.answer(intro_text, parse_mode=ParseMode.HTML, reply_markup=get_gourmet_main_keyboard())


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_mode_exit_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Главное меню")
    await callback.message.answer("🏁 Вы вернулись в <b>Главное меню</b>.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.callback_query(F.data.in_(["gourmet_tip_shelf_beer", "gourmet_tip_shelf_wine_spirits"]))
async def cb_gourmet_shelf_tip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("📸 Сфотографируйте полку")
    is_wine = "wine" in callback.data
    target_state = ActiveModeStates.wine_spirits_mode if is_wine else ActiveModeStates.craft_beer_mode
    await state.set_state(target_state)
    cat = "wine_spirits" if is_wine else "beer"

    text = (
        "📸 <b>ИИ-Сомелье: Подбор напитка по фото полки / витрины / меню</b>\n\n"
        "1. <b>Сделайте фото</b> полки с пивом или алкоголем в магазине (К&Б, Перекрёсток, ВкусВилл, Винлаб, крафтовый бар) или барной карты.\n"
        "2. <b>Отправьте фото сюда в чат</b> (можно с комментарием в подписи: <i>«хочу кислое ягодное»</i>, <i>«красное сухое к стейку»</i> или <i>«до 300 руб»</i>).\n\n"
        "🤖 <i>ИИ-сомелье мгновенно распознает все этикетки, сравнит мировые рейтинги Untappd / Vivino, выберет <b>ТОП-1 напиток</b> на этой полке, назовет безопасную классику и предупредит, чего брать не стоит!</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Случайный сорт", callback_data=f"gourmet_rnd_{cat}"),
                InlineKeyboardButton(text="🍽 Меню кулинарии", callback_data="gourmet_back_to_menu")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


# --- UNIVERSAL DISPATCHER FOR ALL ACTIVE FOOD STATES (TEXT, VOICE, PHOTO) ---

GOURMET_STATE_LIST = [
    ActiveModeStates.breakfast_mode,
    ActiveModeStates.express_meals_mode,
    ActiveModeStates.healthy_fastfood_mode,
    ActiveModeStates.fridge_chef_mode,
    ActiveModeStates.steak_timer_mode,
    ActiveModeStates.shashlik_calc_mode,
    ActiveModeStates.weekly_meal_plan_mode,
    ActiveModeStates.restaurant_sauces_mode,
    ActiveModeStates.asian_cuisine_mode,
    ActiveModeStates.craft_beer_mode,
    ActiveModeStates.wine_spirits_mode,
    ActiveModeStates.barman_mode
]


def _get_category_from_state(current_state_str: str) -> str:
    mapping = {
        "ActiveModeStates:breakfast_mode": "breakfast",
        "ActiveModeStates:express_meals_mode": "express",
        "ActiveModeStates:healthy_fastfood_mode": "fastfood",
        "ActiveModeStates:fridge_chef_mode": "fridge",
        "ActiveModeStates:steak_timer_mode": "steak",
        "ActiveModeStates:shashlik_calc_mode": "shashlik",
        "ActiveModeStates:weekly_meal_plan_mode": "mealplan",
        "ActiveModeStates:restaurant_sauces_mode": "sauces",
        "ActiveModeStates:asian_cuisine_mode": "asian",
        "ActiveModeStates:craft_beer_mode": "beer",
        "ActiveModeStates:wine_spirits_mode": "wine_spirits",
        "ActiveModeStates:barman_mode": "barman"
    }
    return mapping.get(current_state_str, "breakfast")


@router.message(F.state.in_(GOURMET_STATE_LIST))
async def handle_universal_gourmet_input(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    cat = _get_category_from_state(str(current_state))
    user_id = message.from_user.id

    # 1. Voice / Video Note Input Handling (Hands-free kitchen assistant!)
    extracted_text = ""
    if message.voice:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        try:
            file = await message.bot.get_file(message.voice.file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, buf)
            extracted_text = await transcribe_audio_gemini(buf.getvalue(), mime_type="audio/ogg")
            if extracted_text:
                await message.answer(f"🎙 <b>Вы сказали:</b> «<i>{html.escape(extracted_text)}</i>»", parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error transcribing voice in gourmet mode: {e}")
    elif message.video_note:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        try:
            file = await message.bot.get_file(message.video_note.file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, buf)
            extracted_text = await transcribe_audio_gemini(buf.getvalue(), mime_type="video/mp4")
            if extracted_text:
                await message.answer(f"📹 <b>Вы сказали:</b> «<i>{html.escape(extracted_text)}</i>»", parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error transcribing video note in gourmet mode: {e}")
    else:
        extracted_text = message.text or message.caption or ""

    # 2. Check for Exit command
    if is_exit_command(extracted_text):
        await state.clear()
        await message.answer(
            f"🏁 <b>Режим «{CATEGORY_TITLES.get(cat, 'Еда')}» завершен.</b> Вы вернулись в главное меню.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    # 3. Check for "Another recipe" text triggers
    t_lower = extracted_text.strip().lower()
    repeat_triggers = ["еще", "ещё", "другой", "другой рецепт", "другое блюдо", "следующий", "вариант", "дальше", "другое", "покажи еще", "еще вариант"]
    if t_lower in repeat_triggers:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        seen = get_seen_recipes(user_id, cat)
        last_info = get_user_last_gourmet(user_id)
        last_q = last_info.get("query", "")

        data = None
        formatted_text = ""
        if cat == "breakfast":
            data = await generate_express_breakfast(user_id, ingredients=last_q, mood="оригинальный", seen_titles=seen)
            formatted_text = format_breakfast_message(data)
        elif cat == "express":
            data = await generate_15min_meal(user_id, query=last_q, seen_titles=seen)
            formatted_text = format_express_meal_message(data)
        elif cat == "fastfood":
            data = await generate_healthy_fastfood(user_id, dish_query=last_q, seen_titles=seen)
            formatted_text = format_fastfood_message(data)
        elif cat == "fridge":
            data = await cook_from_fridge(user_id, ingredients_text=last_q, seen_titles=seen)
            formatted_text = format_fridge_message(data)
        elif cat == "steak":
            data = await get_steak_guide(user_id, cut=last_q or "Рибай", doneness="Medium", seen_titles=seen)
            formatted_text = format_steak_message(data)
        elif cat == "shashlik":
            data = await calculate_shashlik_marinade(user_id, meat_type=last_q or "Свиная шея", seen_titles=seen)
            formatted_text = format_shashlik_message(data)
        elif cat == "mealplan":
            data = await generate_weekly_meal_plan(user_id, goal=last_q or "ПП", seen_titles=seen)
            formatted_text = format_meal_plan_message(data)
        elif cat == "sauces":
            data = await get_restaurant_sauce(user_id, sauce_name=last_q, seen_titles=seen)
            formatted_text = format_sauce_message(data)
        elif cat == "asian":
            data = await get_asian_dish_recipe(user_id, dish_name=last_q, seen_titles=seen)
            formatted_text = format_asian_message(data)
        elif cat == "beer":
            data = await get_craft_beer_guide(user_id, query=last_q, seen_titles=seen)
            formatted_text = format_craft_beer_message(data)
        elif cat == "wine_spirits":
            data = await get_wine_spirits_guide(user_id, query=last_q, seen_titles=seen)
            formatted_text = format_wine_spirits_message(data)
        elif cat == "barman":
            data = await craft_cocktail(user_id, bar_stock=last_q, seen_titles=seen)
            formatted_text = format_cocktail_message(data)

        if data:
            title = data.get("title") or data.get("steak_title") or data.get("beer_name") or data.get("drink_name") or data.get("plan_title") or "Рецепт"
            add_seen_recipe(user_id, cat, title, full_data=data)
            set_user_last_gourmet(user_id, cat, last_q, full_data=data)

        await message.answer(
            formatted_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_gourmet_result_keyboard(cat, has_shoplist=(cat != "beer" and cat != "wine_spirits"))
        )
        return

    # 4. Photo Input Handling (Meat, Beer, Wine, Fridge, Dish)
    image_bytes = None
    if message.photo:
        try:
            photo = message.photo[-1]
            buf = io.BytesIO()
            await message.bot.download(photo, destination=buf)
            image_bytes = buf.getvalue()
        except Exception as e:
            logger.error(f"Error downloading photo in gourmet mode: {e}")

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    seen = get_seen_recipes(user_id, cat)

    data = None
    formatted_text = ""

    try:
        if cat == "breakfast":
            data = await generate_express_breakfast(user_id, ingredients=extracted_text, seen_titles=seen)
            formatted_text = format_breakfast_message(data)
        elif cat == "express":
            data = await generate_15min_meal(user_id, query=extracted_text, seen_titles=seen)
            formatted_text = format_express_meal_message(data)
        elif cat == "fastfood":
            data = await generate_healthy_fastfood(user_id, dish_query=extracted_text, seen_titles=seen)
            formatted_text = format_fastfood_message(data)
        elif cat == "fridge":
            data = await cook_from_fridge(user_id, ingredients_text=extracted_text, image_bytes=image_bytes, seen_titles=seen)
            formatted_text = format_fridge_message(data)
        elif cat == "steak":
            data = await get_steak_guide(user_id, cut=extracted_text or "Рибай", doneness="по запросу", image_bytes=image_bytes, seen_titles=seen)
            formatted_text = format_steak_message(data)
        elif cat == "shashlik":
            data = await calculate_shashlik_marinade(user_id, meat_type=extracted_text or "Свиная шея", seen_titles=seen)
            formatted_text = format_shashlik_message(data)
        elif cat == "mealplan":
            data = await generate_weekly_meal_plan(user_id, goal=extracted_text or "поддержание формы", seen_titles=seen)
            formatted_text = format_meal_plan_message(data)
        elif cat == "sauces":
            data = await get_restaurant_sauce(user_id, sauce_name=extracted_text, seen_titles=seen)
            formatted_text = format_sauce_message(data)
        elif cat == "asian":
            data = await get_asian_dish_recipe(user_id, dish_name=extracted_text, seen_titles=seen)
            formatted_text = format_asian_message(data)
        elif cat == "beer":
            if image_bytes:
                data = await analyze_alcohol_shelf(user_id, image_bytes=image_bytes, user_preference=extracted_text, alcohol_category="beer")
                formatted_text = format_shelf_advisor_message(data)
            else:
                data = await get_craft_beer_guide(user_id, query=extracted_text, seen_titles=seen)
                formatted_text = format_craft_beer_message(data)
        elif cat == "wine_spirits":
            if image_bytes:
                data = await analyze_alcohol_shelf(user_id, image_bytes=image_bytes, user_preference=extracted_text, alcohol_category="wine_spirits")
                formatted_text = format_shelf_advisor_message(data)
            else:
                data = await get_wine_spirits_guide(user_id, query=extracted_text, seen_titles=seen)
                formatted_text = format_wine_spirits_message(data)
        elif cat == "barman":
            is_non_alc = "безалк" in extracted_text.lower() or "моктейл" in extracted_text.lower()
            data = await craft_cocktail(user_id, bar_stock=extracted_text, non_alcoholic=is_non_alc, seen_titles=seen)
            formatted_text = format_cocktail_message(data)

        if data:
            top_p = data.get("top_pick")
            top_name = top_p.get("name") if isinstance(top_p, dict) else None
            title = data.get("title") or data.get("steak_title") or data.get("beer_name") or data.get("drink_name") or top_name or data.get("plan_title") or extracted_text or "Рецепт"
            add_seen_recipe(user_id, cat, title, full_data=data)
            set_user_last_gourmet(user_id, cat, extracted_text, full_data=data)

        await message.answer(
            formatted_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_gourmet_result_keyboard(cat, has_shoplist=(cat != "beer" and cat != "wine_spirits" or image_bytes is not None))
        )
    except Exception as e:
        logger.error(f"Error handling gourmet dialog for {cat}: {e}")
        await message.answer(
            f"⚠️ Не удалось сформировать рецепт: {e}. Попробуйте уточнить запрос или выберите готовый пресет:",
            reply_markup=get_category_presets_keyboard(cat)
        )
