import re
import io
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
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

logger = logging.getLogger("GourmetHandlers")
router = Router(name="gourmet_assistant")


def get_gourmet_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍳 Завтрак за 10 мин", callback_data="mode_start_breakfast"),
                InlineKeyboardButton(text="⚡️ Блюда за 15 мин", callback_data="mode_start_express")
            ],
            [
                InlineKeyboardButton(text="🌯 ПП-Фастфуд", callback_data="mode_start_fastfood"),
                InlineKeyboardButton(text="🧊 Шеф из холодильника", callback_data="mode_start_fridge")
            ],
            [
                InlineKeyboardButton(text="🥩 Таймер стейков", callback_data="mode_start_steak"),
                InlineKeyboardButton(text="🍢 Маринад шашлыка", callback_data="mode_start_shashlik")
            ],
            [
                InlineKeyboardButton(text="📅 Меню на неделю + Список", callback_data="mode_start_mealplan"),
                InlineKeyboardButton(text="🥫 Соусы шефов", callback_data="mode_start_sauces")
            ],
            [
                InlineKeyboardButton(text="🍜 Азиатская кухня", callback_data="mode_start_asian"),
                InlineKeyboardButton(text="🍺 Пивной сомелье", callback_data="mode_start_beer")
            ],
            [
                InlineKeyboardButton(text="🍷 Вино, Водка, Коньяк & Алкоголь", callback_data="mode_start_wine_spirits")
            ],
            [
                InlineKeyboardButton(text="🍸 AI-Бармен & Коктейли", callback_data="mode_start_barman")
            ]
        ]
    )


# --- FORMATTERS ---

def format_breakfast_message(data: dict) -> str:
    lines = [
        f"🍳 <b>{data.get('title', 'Экспресс-завтрак')}</b>",
        f"⏱ Время: <b>{data.get('prep_time', '10 мин')}</b> | ⚡️ КБЖУ: <b>{data.get('calories', 400)} ккал</b> (Б: {data.get('protein', 20)}г | Ж: {data.get('fats', 15)}г | У: {data.get('carbs', 25)}г)",
        "",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")
    lines.append("")
    lines.append("👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("chef_tip"):
        lines.append("")
        lines.append(f"{data['chef_tip']}")
    lines.append("")
    lines.append("💬 <i>Вы в режиме завтраков. Напишите пожелания (например: «без яиц», «больше белка», «из творога»):</i>")
    return "\n".join(lines)


def format_fastfood_message(data: dict) -> str:
    lines = [
        f"🌯 <b>{data.get('title', 'ПП-Фастфуд')}</b>",
        f"⏱ Время: <b>{data.get('prep_time', '15 мин')}</b> | ⚡️ КБЖУ: <b>{data.get('calories', 400)} ккал</b> (Б: {data.get('protein', 30)}г | Ж: {data.get('fats', 12)}г | У: {data.get('carbs', 40)}г)",
        f"🔥 <i>{data.get('fastfood_comparison', 'В 2 раза меньше калорий!')}</i>",
        "",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")
    lines.append("")
    lines.append("👨‍🍳 <b>Технология приготовления:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("chef_secret"):
        lines.append("")
        lines.append(f"{data['chef_secret']}")
    lines.append("")
    lines.append("💬 <i>Напишите, какой фастфуд приготовить полезно (например: «бургер из индейки», «наггетсы в хлопьях», «пицца на лаваше»):</i>")
    return "\n".join(lines)


def format_fridge_message(data: dict) -> str:
    lines = [
        "🧊 <b>Шеф по холодильнику — Готовим из того, что есть:</b>",
        f"💬 <i>{data.get('fridge_summary', 'Вот 3 варианта блюд:')}</i>",
        ""
    ]
    for i, r in enumerate(data.get("recipes", []), 1):
        lines.append(f"<b>{r.get('name', f'Рецепт {i}')}</b>")
        lines.append(f"⏱ <b>{r.get('time', '10 мин')}</b> | ⚡️ <b>{r.get('calories', 400)} ккал</b>")
        used = ', '.join(r.get('used_ingredients', []))
        lines.append(f"🛒 Продукты: <i>{used}</i>")
        lines.append(f"📝 {r.get('instructions', '')}")
        lines.append("")
    if data.get("pro_tip"):
        lines.append(f"{data['pro_tip']}")
    lines.append("")
    lines.append("💬 <i>Отправьте список продуктов текстом или пришлите ФОТО открытого холодильника — я составлю новые рецепты!</i>")
    return "\n".join(lines)


def format_steak_message(data: dict) -> str:
    lines = [
        f"🥩 <b>{data.get('steak_title', 'Стейк')}</b>",
        f"🌡 Целевая температура внутри: <b>{data.get('target_core_temp', '54-56°C')}</b>",
        f"⏱ Обжарка корочки: <b>{data.get('crust_sear_time', 'По 2 мин с каждой стороны')}</b>",
        f"🧈 Бастинг (масло + травы): <b>{data.get('basting_time', '1-1.5 мин')}</b>",
        f"⏳ Отдых мяса: <b>{data.get('rest_time', '5 минут под фольгой')}</b>",
        "",
        "👨‍🍳 <b>Пошаговая инструкция шефа:</b>"
    ]
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("chef_rule"):
        lines.append("")
        lines.append(f"{data['chef_rule']}")
    lines.append("")
    lines.append("💬 <i>Напишите отруб, толщину или желаемую прожарку (например: «Стриплойн 3 см Medium», «Филе-миньон Rare»):</i>")
    return "\n".join(lines)


def format_express_meal_message(data: dict) -> str:
    lines = [
        f"⚡️ <b>{data.get('title', 'Блюдо за 15 минут')}</b>",
        f"⏱ Время: <b>{data.get('prep_time', '15 минут')}</b> | 🍳 Посуда: <b>{data.get('utensils', '1 сковорода')}</b>",
        f"⚡️ КБЖУ: <b>{data.get('calories', 500)} ккал</b> (Б: {data.get('protein', 35)}г | Ж: {data.get('fats', 15)}г | У: {data.get('carbs', 50)}г)",
        "",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")
    lines.append("")
    lines.append("👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("express_hack"):
        lines.append("")
        lines.append(f"{data['express_hack']}")
    lines.append("")
    lines.append("💬 <i>Напишите пожелание по экспресс-блюду (например: «быстрый ужин из рыбы», «вок с говядиной за 15 мин»):</i>")
    return "\n".join(lines)


def format_meal_plan_message(data: dict) -> str:
    lines = [
        f"📅 <b>{data.get('plan_title', 'Недельный рацион ПП')}</b>",
        ""
    ]
    for d in data.get("days", []):
        lines.append(f"🗓 <b>{d.get('day')}:</b>")
        lines.append(f"   🌅 Завтрак: {d.get('breakfast')}")
        lines.append(f"   ☀️ Обед: {d.get('lunch')}")
        lines.append(f"   🌙 Ужин: {d.get('dinner')}")
        lines.append("")
    lines.append("🛒 <b>АВТОМАТИЧЕСКИЙ СПИСОК ПОКУПОК НА НЕДЕЛЮ:</b>")
    shop = data.get("shopping_list", {})
    for cat, items in shop.items():
        lines.append(f"<b>{cat}:</b>")
        for it in items:
            lines.append(f"   ▫️ {it}")
    if data.get("mealprep_tip"):
        lines.append("")
        lines.append(f"{data['mealprep_tip']}")
    lines.append("")
    lines.append("💬 <i>Напишите свою цель (например: «набор массы 2500 ккал», «похудение 1700 ккал», «без рыбы/молочки»):</i>")
    return "\n".join(lines)


def format_shashlik_message(data: dict) -> str:
    lines = [
        f"🍢 <b>{data.get('title', 'Маринад для шашлыка')}</b>",
        f"⏳ Время маринования: <b>{data.get('marinade_time', '4-6 часов')}</b>",
        f"🔥 Расход углей: <b>{data.get('coals_needed', '1 мешок (2.5-3 кг)')}</b>",
        "",
        "⚖️ <b>Точные пропорции ингредиентов:</b>"
    ]
    for prop in data.get("proportions", []):
        lines.append(f"  • {prop}")
    lines.append("")
    lines.append("👨‍🍳 <b>Технология маринования и жарки:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("grill_secrets"):
        lines.append("")
        lines.append(f"{data['grill_secrets']}")
    lines.append("")
    lines.append("💬 <i>Напишите тип мяса и вес (например: «Куриные бедра 3 кг», «Баранина 1.5 кг в гранатовом соке»):</i>")
    return "\n".join(lines)


def format_sauce_message(data: dict) -> str:
    lines = [
        f"🥫 <b>{data.get('title', 'Соус шеф-повара')}</b>",
        f"🍽 Сочетаемость: <i>{data.get('pairing', 'Ко всем блюдам')}</i>",
        f"⏱ Время: <b>{data.get('prep_time', '7 мин')}</b> | ❄️ Хранение: <b>{data.get('shelf_life', '2 недели')}</b>",
        "",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")
    lines.append("")
    lines.append("👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("sauce_secret"):
        lines.append("")
        lines.append(f"{data['sauce_secret']}")
    lines.append("")
    lines.append("💬 <i>Напишите название соуса (например: «Бешамель», «Голландез к яйцам пашот», «Терияки домашний», «Тартар»):</i>")
    return "\n".join(lines)


def format_asian_message(data: dict) -> str:
    lines = [
        f"🍜 <b>{data.get('title', 'Азиатское блюдо')}</b>",
        f"🌏 Страна: <b>{data.get('country', 'Азия')}</b> | 🌶 Острота: <b>{data.get('spiciness', 'Средняя')}</b>",
        f"⏱ Время: <b>{data.get('prep_time', '25 мин')}</b> | ⚡️ КБЖУ: <b>{data.get('calories', 500)} ккал</b>",
        "",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")
    lines.append("")
    lines.append("👨‍🍳 <b>Пошаговый вок-рецепт:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")
    if data.get("asian_secret"):
        lines.append("")
        lines.append(f"{data['asian_secret']}")
    lines.append("")
    lines.append("💬 <i>Напишите азиатское блюдо (например: «Том Ям с креветками», «Фо Бо с говядиной», «Пад Тай с курицей», «Кимчи»):</i>")
    return "\n".join(lines)


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


def format_craft_beer_message(data: dict) -> str:
    fn = data.get("flavor_notes", "")
    if isinstance(fn, list):
        fn_str = ", ".join(str(x) for x in fn)
    else:
        fn_str = str(fn) if fn else "Солодовые и хмелевые ноты"
    fn_str = translate_flavor_notes(fn_str)

    lines = [
        f"🍺 <b>{data.get('beer_name', 'Крафтовое пиво')}</b>",
        f"🏭 Пивоварня: <b>{data.get('brewery', 'Крафтовая')}</b> | Стиль: <i>{data.get('style', 'Ale')}</i>",
        f"📊 Крепость: <b>{data.get('abv', '5.0%')}</b> | Горечь: <b>{data.get('ibu', '20 IBU')}</b> | ⭐️ <b>Untappd: {data.get('untappd_rating', '4.0/5')}</b>",
        "",
        f"👅 <b>Вкусное или нет? (Консенсус отзывов):</b>\n{data.get('taste_verdict', '')}",
        "",
        f"🛒 <b>Вердикт сомелье:</b>\n{data.get('buy_verdict', '')}",
        "",
        "🍟 <b>ИДЕАЛЬНЫЕ ЗАКУСКИ (FOOD PAIRING):</b>"
    ]
    snacks = data.get("snacks", {})
    snack_lines = []
    if isinstance(snacks, dict):
        croutons = snacks.get("croutons") or snacks.get("crouton") or snacks.get("сухарики") or snacks.get("гренки") or snacks.get("bread")
        fish = snacks.get("fish") or snacks.get("seafood") or snacks.get("рыба") or snacks.get("морепродукты") or snacks.get("fish_seafood")
        chips = snacks.get("chips") or snacks.get("crisps") or snacks.get("чипсы") or snacks.get("снеки") or snacks.get("snacks")
        hot_food = snacks.get("hot_food") or snacks.get("hot") or snacks.get("dishes") or snacks.get("cheese") or snacks.get("сыр") or snacks.get("горячее") or snacks.get("meat")

        if croutons:
            snack_lines.append(f"  🍞 <b>Сухарики/гренки:</b> <i>{croutons}</i>")
        if fish:
            snack_lines.append(f"  🐟 <b>Рыбка/морепродукты:</b> <i>{fish}</i>")
        if chips:
            snack_lines.append(f"  🥔 <b>Чипсы/снеки:</b> <i>{chips}</i>")
        if hot_food:
            snack_lines.append(f"  🍔 <b>Горячее/сыры:</b> <i>{hot_food}</i>")

        if not snack_lines:
            for k, v in snacks.items():
                if v:
                    snack_lines.append(f"  • <b>{k.replace('_', ' ').capitalize()}:</b> <i>{v}</i>")
    elif isinstance(snacks, list):
        for s in snacks:
            if s:
                snack_lines.append(f"  • <i>{s}</i>")
    elif isinstance(snacks, str) and snacks.strip():
        snack_lines.append(f"  🍿 <i>{snacks.strip()}</i>")

    if not snack_lines:
        snack_lines = [
            "  🍞 <b>Сухарики/гренки:</b> <i>Чесночные бородинские гренки с сырным соусом</i>",
            "  🐟 <b>Рыбка/морепродукты:</b> <i>Вяленая горбуша, корюшка или кольца кальмара</i>",
            "  🍔 <b>Горячее/сыры:</b> <i>Сочный бургер, крылышки Баффало, сыр Чеддер</i>"
        ]

    lines.extend(snack_lines)

    hang = data.get("hangover_risk", {})
    if isinstance(hang, dict) and hang:
        lines.append("")
        lines.append("🤕 <b>БУДЕТ ЛИ УТРОМ БОЛЕТЬ ГОЛОВА? (Похмельный фактор):</b>")
        lines.append(f"  • Риск: <b>{hang.get('risk_level', 'Низкий')}</b>")
        lines.append(f"  • Прогноз: <i>{hang.get('morning_forecast', '')}</i>")
        if hang.get("hangover_cure"):
            lines.append(f"  • {hang.get('hangover_cure')}")

    lines.append("")
    lines.append(f"🌿 Вкусовые ноты: <i>{fn_str}</i> | ❄️ Подача: <b>{data.get('serving_temp', '6-8°C')}</b>")
    lines.append("")
    lines.append("💬 <i>Вы в режиме сомелье. Пришлите ФОТО банки/этикетки пива или напишите название — я сделаю мгновенный разбор!</i>")
    return "\n".join(lines)


def format_cocktail_message(data: dict) -> str:
    lines = [
        f"🍸 <b>{data.get('title', 'Коктейль')}</b>",
        f"🏷 Стиль: <i>{data.get('category', 'Классика')}</i> | Крепость: <b>{data.get('strength', '12%')}</b>",
        f"🥃 Бокал: <i>{data.get('glassware', 'Хайбол со льдом')}</i>",
        "",
        "🧊 <b>Состав и пропорции:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")
    lines.append("")
    lines.append("🍹 <b>Метод приготовления:</b>")
    for step in data.get("recipe_steps", []):
        lines.append(f"  {step}")
    if data.get("barman_secret"):
        lines.append("")
        lines.append(f"{data['barman_secret']}")
    lines.append("")
    lines.append("💬 <i>Напишите ваши напитки или пожелание (например: «хочу покислее», «добавь виски», «безалкогольный моктейль»):</i>")
    return "\n".join(lines)


def format_wine_spirits_message(data: dict) -> str:
    notes = data.get("tasting_notes", "")
    if isinstance(notes, list):
        notes_str = ", ".join(str(x) for x in notes)
    else:
        notes_str = str(notes) if notes else "Благородный сбалансированный букет"
    notes_str = translate_flavor_notes(notes_str)

    lines = [
        f"🍷 <b>{data.get('drink_name', 'Алкогольный напиток')}</b>",
        f"🏭 Производитель: <b>{data.get('producer', 'Мастер')}</b> | Категория: <i>{data.get('category', 'Премиум')}</i>",
        f"🌍 Регион: <i>{data.get('origin', 'Мир')}</i> | Крепость: <b>{data.get('abv', '40%')}</b> | ⭐️ <b>Рейтинг: {data.get('rating', '4.2 / 5.0')}</b>",
        "",
        f"👅 <b>Вкус и мягкость (Консенсус отзывов):</b>\n{data.get('taste_verdict', '')}",
        "",
        f"🛒 <b>Вердикт сомелье:</b>\n{data.get('buy_verdict', '')}",
        "",
        "🧀 <b>ИДЕАЛЬНЫЕ ГАСТРОНОМИЧЕСКИЕ ПАРЫ:</b>"
    ]
    pairings = data.get("pairings", {})
    pairing_lines = []
    if isinstance(pairings, dict):
        cheeses_meats = pairings.get("cheeses_meats") or pairings.get("cheese") or pairings.get("meat") or pairings.get("сыры") or pairings.get("мясо")
        hot_dishes = pairings.get("hot_dishes") or pairings.get("hot") or pairings.get("main_dishes") or pairings.get("горячее") or pairings.get("блюда")
        traditional = pairings.get("traditional_snacks") or pairings.get("snacks") or pairings.get("traditional") or pairings.get("закуски")
        fruits = pairings.get("fruits_desserts") or pairings.get("desserts") or pairings.get("fruits") or pairings.get("десерты") or pairings.get("фрукты")

        if cheeses_meats:
            pairing_lines.append(f"  🧀 <b>Сыры/Мясные деликатесы:</b> <i>{cheeses_meats}</i>")
        if hot_dishes:
            pairing_lines.append(f"  🥩 <b>Горячие блюда:</b> <i>{hot_dishes}</i>")
        if traditional:
            pairing_lines.append(f"  🍋 <b>Закуски под крепкое:</b> <i>{traditional}</i>")
        if fruits:
            pairing_lines.append(f"  🥖 <b>Десерты/Фрукты:</b> <i>{fruits}</i>")

        if not pairing_lines:
            for k, v in pairings.items():
                if v:
                    pairing_lines.append(f"  • <b>{k.replace('_', ' ').capitalize()}:</b> <i>{v}</i>")
    elif isinstance(pairings, list):
        for p in pairings:
            if p:
                pairing_lines.append(f"  • <i>{p}</i>")
    elif isinstance(pairings, str) and pairings.strip():
        pairing_lines.append(f"  🍽 <i>{pairings.strip()}</i>")

    if not pairing_lines:
        pairing_lines = [
            "  🧀 <b>Сыры/Мясные деликатесы:</b> <i>Сырная тарелка (Пармезан, Гауда), сыровяленый окорок</i>",
            "  🥩 <b>Горячие блюда:</b> <i>Стейк из говядины или запеченная утка с яблоками</i>"
        ]

    lines.extend(pairing_lines)

    hang = data.get("hangover_risk", {})
    if isinstance(hang, dict) and hang:
        lines.append("")
        lines.append("🤕 <b>БУДЕТ ЛИ УТРОМ БОЛЕТЬ ГОЛОВА? (Похмельный фактор):</b>")
        lines.append(f"  • Риск: <b>{hang.get('risk_level', 'Умеренный')}</b>")
        lines.append(f"  • Прогноз: <i>{hang.get('morning_forecast', '')}</i>")
        if hang.get("safety_rule"):
            lines.append(f"  • {hang.get('safety_rule')}")

    lines.append("")
    lines.append(f"🌿 Букет: <i>{notes_str}</i> | ❄️ Подача: <b>{data.get('serving', 'Комнатная / Охлажденным')}</b>")
    lines.append("")
    lines.append("💬 <i>Вы в режиме сомелье. Пришлите ФОТО бутылки/этикетки (вино, водка, коньяк, виски, ром и др.) или напишите название — я сделаю мгновенный разбор!</i>")
    return "\n".join(lines)


# --- MAIN ENTRY POINT ---

@router.message(Command("gourmet"))
@router.message(Command("breakfast"))
@router.message(Command("barman"))
@router.message(Command("food"))
@router.message(F.text.in_(["🍽 Еда", "🍳 Еда", "Еда", "еда", "🍳 Завтрак & 🍸 Бармен", "🍳 Экспресс-Завтраки", "🍸 AI-Бармен", "🍳 Кулинарный шеф", "🍽 Кулинария & Бар"]))
async def cmd_gourmet_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🍳 <b>Гранд-Шеф & 🍸 AI-Бармен — Персональный кулинарный центр:</b>\n\n"
        "Выберите направление:\n"
        "• <b>🍳 Завтраки & ⚡️ Блюда за 15 мин</b> — экспресс-кулинария для занятых людей.\n"
        "• <b>🌯 ПП-Фастфуд</b> — любимая шаверма, бургеры и пицца без вреда для фигуры.\n"
        "• <b>🧊 Шеф из холодильника</b> — рецепты по фото или списку остатков продуктов.\n"
        "• <b>🥩 Таймер стейков & 🍢 Маринад шашлыка</b> — мясная школа идеальной сочности.\n"
        "• <b>📅 Рацион на неделю + Список</b> — меню ПП и готовый список в супермаркет.\n"
        "• <b>🥫 Соусы шефов & 🍜 Азиатская кухня</b> — ресторанный уровень дома.\n"
        "• <b>🍸 AI-Бармен & 🍺 Крафтовое пиво</b> — гид по стилям и авторские миксы.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_gourmet_main_keyboard()
    )


# --- CALLBACK LAUNCHERS ---

@router.callback_query(F.data == "mode_start_breakfast")
async def cb_start_breakfast(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.breakfast_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await generate_express_breakfast(user_id, ingredients="", mood="бодрый и сытный")
    text = format_breakfast_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Завтрак"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_fastfood")
async def cb_start_fastfood(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.healthy_fastfood_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await generate_healthy_fastfood(user_id)
    text = format_fastfood_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("ПП-Фастфуд"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_fridge")
async def cb_start_fridge(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.fridge_chef_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await cook_from_fridge(user_id)
    text = format_fridge_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Шеф-Холодильник"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_steak")
async def cb_start_steak(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.steak_timer_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_steak_guide(user_id)
    text = format_steak_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Стейки"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_express")
async def cb_start_express(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.express_meals_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await generate_15min_meal(user_id)
    text = format_express_meal_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Блюда за 15 мин"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_mealplan")
async def cb_start_mealplan(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.weekly_meal_plan_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await generate_weekly_meal_plan(user_id)
    text = format_meal_plan_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Меню на неделю"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_shashlik")
async def cb_start_shashlik(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.shashlik_calc_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await calculate_shashlik_marinade(user_id)
    text = format_shashlik_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Шашлык"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_sauces")
async def cb_start_sauces(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.restaurant_sauces_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_restaurant_sauce(user_id)
    text = format_sauce_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Соусы"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_asian")
async def cb_start_asian(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.asian_cuisine_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_asian_dish_recipe(user_id)
    text = format_asian_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Азиатская кухня"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_beer")
async def cb_start_beer(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.craft_beer_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_craft_beer_guide(user_id)
    text = format_craft_beer_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Крафтовое пиво"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_wine_spirits")
async def cb_start_wine_spirits(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.wine_spirits_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await get_wine_spirits_guide(user_id)
    text = format_wine_spirits_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Вино & Крепкое"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_barman")
async def cb_start_barman(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.barman_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock="джин, виски, ром, тоник, сок, цитрусовые, мята, лед", non_alcoholic=False)
    text = format_cocktail_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("AI-Бармен"))
    await callback.answer()


# --- DIALOG & INPUT HANDLERS ---

@router.message(ActiveModeStates.breakfast_mode)
async def handle_breakfast_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Завтрак» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await generate_express_breakfast(user_id, ingredients=text, mood="по запросу пользователя")
    reply = format_breakfast_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Завтрак"))


@router.message(ActiveModeStates.healthy_fastfood_mode)
async def handle_fastfood_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «ПП-Фастфуд» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await generate_healthy_fastfood(user_id, dish_query=text)
    reply = format_fastfood_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("ПП-Фастфуд"))


@router.message(ActiveModeStates.fridge_chef_mode)
async def handle_fridge_dialog(message: types.Message, state: FSMContext):
    text = message.text or message.caption or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Шеф-Холодильник» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    status_msg = None
    try:
        if message.photo:
            status_msg = await message.answer("🧊 <i>Распознаю продукты на фото вашего холодильника и придумываю 3 блюда...</i>", parse_mode=ParseMode.HTML)
            photo = message.photo[-1]
            buf = io.BytesIO()
            await message.bot.download(photo, destination=buf)
            image_bytes = buf.getvalue()
            data = await cook_from_fridge(user_id, image_bytes=image_bytes)
        else:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            data = await cook_from_fridge(user_id, ingredients_text=text)

        reply = format_fridge_message(data)
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

        try:
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Шеф-Холодильник"))
        except Exception:
            await message.answer(reply, reply_markup=get_mode_keyboard("Шеф-Холодильник"))

    except Exception as e:
        logger.error(f"Error in handle_fridge_dialog: {e}")
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        await message.answer(f"⚠️ Ошибка обработки: {e}. Попробуйте отправить другое фото или список продуктов текстом.", reply_markup=get_mode_keyboard("Шеф-Холодильник"))


@router.message(ActiveModeStates.steak_timer_mode)
async def handle_steak_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Стейки» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_steak_guide(user_id, cut=text, doneness="по запросу")
    reply = format_steak_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Стейки"))


@router.message(ActiveModeStates.express_meals_mode)
async def handle_express_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Блюда за 15 мин» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await generate_15min_meal(user_id, query=text)
    reply = format_express_meal_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Блюда за 15 мин"))


@router.message(ActiveModeStates.weekly_meal_plan_mode)
async def handle_mealplan_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Меню на неделю» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await generate_weekly_meal_plan(user_id, goal=text)
    reply = format_meal_plan_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Меню на неделю"))


@router.message(ActiveModeStates.shashlik_calc_mode)
async def handle_shashlik_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Шашлык» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await calculate_shashlik_marinade(user_id, meat_type=text)
    reply = format_shashlik_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Шашлык"))


@router.message(ActiveModeStates.restaurant_sauces_mode)
async def handle_sauces_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Соусы» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_restaurant_sauce(user_id, sauce_name=text)
    reply = format_sauce_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Соусы"))


@router.message(ActiveModeStates.asian_cuisine_mode)
async def handle_asian_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Азиатская кухня» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await get_asian_dish_recipe(user_id, dish_name=text)
    reply = format_asian_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Азиатская кухня"))


@router.message(ActiveModeStates.craft_beer_mode)
async def handle_beer_dialog(message: types.Message, state: FSMContext):
    text = message.text or message.caption or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Крафтовое пиво» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    status_msg = None
    try:
        if message.photo:
            status_msg = await message.answer("🍺 <i>Изучаю фото этикетки, ищу отзывы в Untappd и рассчитываю похмельный индекс...</i>", parse_mode=ParseMode.HTML)
            photo = message.photo[-1]
            buf = io.BytesIO()
            await message.bot.download(photo, destination=buf)
            image_bytes = buf.getvalue()
            data = await get_craft_beer_guide(user_id, image_bytes=image_bytes)
        else:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            data = await get_craft_beer_guide(user_id, query=text)

        reply = format_craft_beer_message(data)
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

        try:
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Крафтовое пиво"))
        except Exception:
            await message.answer(reply, reply_markup=get_mode_keyboard("Крафтовое пиво"))

    except Exception as e:
        logger.error(f"Error in handle_beer_dialog: {e}")
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        await message.answer(f"⚠️ Ошибка обработки: {e}. Попробуйте отправить другое фото или написать название пива текстом.", reply_markup=get_mode_keyboard("Крафтовое пиво"))


@router.message(ActiveModeStates.wine_spirits_mode)
async def handle_wine_spirits_dialog(message: types.Message, state: FSMContext):
    text = message.text or message.caption or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Вино & Крепкое» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    status_msg = None
    try:
        if message.photo:
            status_msg = await message.answer("🍷 <i>Изучаю фото этикетки, ищу оценки на Vivino / Whiskybase и рассчитываю похмельный индекс...</i>", parse_mode=ParseMode.HTML)
            photo = message.photo[-1]
            buf = io.BytesIO()
            await message.bot.download(photo, destination=buf)
            image_bytes = buf.getvalue()
            data = await get_wine_spirits_guide(user_id, image_bytes=image_bytes)
        else:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            data = await get_wine_spirits_guide(user_id, query=text)

        reply = format_wine_spirits_message(data)
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

        try:
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Вино & Крепкое"))
        except Exception:
            await message.answer(reply, reply_markup=get_mode_keyboard("Вино & Крепкое"))

    except Exception as e:
        logger.error(f"Error in handle_wine_spirits_dialog: {e}")
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass
        await message.answer(f"⚠️ Ошибка обработки: {e}. Попробуйте отправить другое фото или написать название напитка текстом.", reply_markup=get_mode_keyboard("Вино & Крепкое"))


@router.message(ActiveModeStates.barman_mode)
async def handle_barman_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «AI-Бармен» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return
    user_id = message.from_user.id
    is_non_alcol = "безалк" in text.lower() or "моктейл" in text.lower()
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock=text, non_alcoholic=is_non_alcol)
    reply = format_cocktail_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("AI-Бармен"))

