import re
import json
import html
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("AlcoholShelfAdvisor")


async def analyze_alcohol_shelf(
    user_id: int,
    image_bytes: bytes,
    user_preference: str = "",
    alcohol_category: str = "beer_or_wine"
) -> Dict[str, Any]:
    """
    AI Sommelier Shelf and Drink Advisor:
    Analyzes supermarket shelves, craft beer shops, wine racks, or bar drink menus from photos.
    Identifies visible bottles/cans, cross-references ratings (Untappd, Vivino, Whiskybase),
    and gives actionable purchase advice:
    - #1 Best Pick on the shelf (taste, rating, value)
    - #2 Safe/Classic Pick (smoother or traditional choice)
    - #3 Adventurous/Wildcard Pick (unique, sour, imperial or rare craft)
    - Avoid list (overpriced, watery or harsh drinks to skip)
    - Perfect Food Pairing for the winner
    - Hangover risk assessment
    """
    pref_instruction = ""
    if user_preference:
        pref_instruction = f"\nПРЕДПОЧТЕНИЕ ПОЛЬЗОВАТЕЛЯ: '{user_preference}'. Обязательно выбери среди напитков на фото то, что максимально точно соответствует этому пожеланию!"

    prompt = (
        "Ты мировой гранд-сомелье (Master Sommelier) и главный пивной эксперт (Master Cicerone).\n"
        "Пользователь прислал ФОТО: это витрина/полка магазина (крафтовое пиво, винотека, виски, водка, коньяк, сидр), "
        "барная карта, меню кранов или несколько стоящих рядом бутылок.\n"
        f"{pref_instruction}\n\n"
        "ТВОЯ ЗАДАЧА:\n"
        "1. Внимательно осмотри фото и распознай ВСЕ различимые бутылки, банки, краны или пункты меню.\n"
        "2. Сравни их рейтинги по мировым алкогольным базам (Untappd для пива/сидра, Vivino для вина, Whiskybase/Distiller для крепкого).\n"
        "3. Выбери АБСОЛЮТНО ЛУЧШИЙ напиток на этой полке/фото и аргументируй выбор.\n"
        "4. Предложи более спокойную альтернативу (Safe Pick) и смелый эксперимент (Wildcard Pick).\n"
        "5. Укажи 1-2 бутылки с этого фото, которые ЛУЧШЕ НЕ БРАТЬ (спиртуозные, химозные, водянистые или с плохими отзывами).\n"
        "6. Подбери идеальную закуску и оцени риск утреннего похмелья для топ-выбора.\n\n"
        "ВАЖНО: Если на фото видна только ОДНА бутылка/банка — сделай ее разбор в 'top_pick', объясни стоит ли ее брать, "
        "а в 'safe_pick' и 'wildcard_pick' укажи похожие альтернативы.\n\n"
        "Верни СТРОГО валидный JSON следующей структуры (без лишнего текста вокруг):\n"
        "{\n"
        '  "shelf_overview": "Полка крафтового и импортного пива в супермаркете (замечены IPA, стауты, лагеры)",\n'
        '  "top_pick": {\n'
        '    "name": "🍺 Zagovor - Decontrol / 🍷 Campo Viejo Rioja Reserva",\n'
        '    "style_type": "Double NEIPA, 8.0% / Красное сухое Темпранильо, 13.5%",\n'
        '    "rating": "4.15 / 5.0 ⭐️ (Untappd / Vivino)",\n'
        '    "why_choose": "Лучшее соотношение свежести, богатого тела и хмелевой ароматики на этой витрине.",\n'
        '    "taste_profile": "Яркие тропические фрукты (манго, маракуйя), сочный грейпфрут и мягкая кремовая текстура без выпирающего спирта.",\n'
        '    "ideal_snack": "Бородинские чесночные гренки, острые крылышки или сыр Чеддер"\n'
        '  },\n'
        '  "safe_pick": {\n'
        '    "name": "🍺 Pilsner Urquell / 🍷 Chianti Classico",\n'
        '    "style_type": "Чешский светлый лагер, 4.4% / Сухое красное, 13.0%",\n'
        '    "rating": "3.75 / 5.0 ⭐️",\n'
        '    "reason": "Надежная классика с чистым солодовым вкусом и легкой благородной горчинкой. Понравится всем."\n'
        '  },\n'
        '  "wildcard_pick": {\n'
        '    "name": "🍓 4Brewers - Доза / 🥃 Laphroaig 10",\n'
        '    "style_type": "Фруктовый кислый смузи-эль / Торфяной островной виски",\n'
        '    "rating": "4.2 / 5.0 ⭐️",\n'
        '    "reason": "Для тех, кто хочет ярких эмоций: взрывной фруктовый вкус пюре манго и маракуйи с легкой кислинкой."\n'
        '  },\n'
        '  "avoid_picks": [\n'
        '    "Балтика 9 или крепкий бюджетный лагер (спиртуозный профиль, тяжелое похмелье)",\n'
        '    "Сладкие псевдо-винные напитки в нижнем ряду (много сахара и красителей)"\n'
        '  ],\n'
        '  "hangover_forecast": {\n'
        '    "risk_level": "🟢 Низкий (при 1-2 порциях) / 🟡 Средний (при 3+)",\n'
        '    "advice": "Пейте 1 стакан негазированной воды на каждую банку/бокал, чтобы утро было свежим."\n'
        '  },\n'
        '  "shopping_checklist": [\n'
        '    "Пиво Zagovor Decontrol (1-2 банки)",\n'
        '    "Чесночные гренки или нарезка сыра Чеддер",\n'
        '    "Бутылка минеральной воды без газа"\n'
        '  ]\n'
        "}"
    )

    try:
        resp = await ask_gemini(user_id, prompt, image_bytes=image_bytes)
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error in analyze_alcohol_shelf: {e}")

    # Fallback response if image analysis had an unexpected format
    return {
        "shelf_overview": "Полка с пивом и напитками в магазине",
        "top_pick": {
            "name": "🍺 Топовый крафтовый эль / Премиальное вино",
            "style_type": "Качественный сорт со сбалансированным вкусом",
            "rating": "4.1 / 5.0 ⭐️",
            "why_choose": "Лучший выбор по отзывам знатоков и рейтингу среди видимого ассортимента.",
            "taste_profile": "Насыщенный, гармоничный вкус без неприятной резкой спиртуозности.",
            "ideal_snack": "Сырная нарезка, слабосоленая рыба или мясные деликатесы."
        },
        "safe_pick": {
            "name": "🍺 Классический немецкий/чешский пилснер",
            "style_type": "Светлый лагер",
            "rating": "3.8 / 5.0 ⭐️",
            "reason": "Беспроигрышный выбор: легкое, освежающее тело и приятная хмелевая горчинка."
        },
        "wildcard_pick": {
            "name": "🍓 Ягодный Sour Ale / Сидр прямого отжима",
            "style_type": "Кислый сорт или натуральный брют",
            "rating": "4.0 / 5.0 ⭐️",
            "reason": "Для ярких впечатлений: натуральные соки, свежая ягодная кислинка."
        },
        "avoid_picks": [
            "Дешевые крепленые сорта с добавлением спирта и патоки",
            "Пластиковые баклажки массовых брендов (водянистый невыразительный вкус)"
        ],
        "hangover_forecast": {
            "risk_level": "🟢 Низкий при соблюдении меры",
            "advice": "Пейте чистую воду параллельно с напитком!"
        },
        "shopping_checklist": [
            "Выбранный качественный сорт",
            "Свежие закуски (сыр, гренки, оливки)",
            "Вода без газа"
        ]
    }


def format_shelf_advisor_message(data: dict) -> str:
    """Formats the shelf analysis JSON into an informative, premium Telegram message."""
    overview = html.escape(str(data.get("shelf_overview", "Ассортимент напитков")))
    top = data.get("top_pick", {})
    safe = data.get("safe_pick", {})
    wild = data.get("wildcard_pick", {})
    avoid = data.get("avoid_picks", [])
    hangover = data.get("hangover_forecast", {})

    lines = [
        "📸 <b>ВЕРДИКТ СОМЕЛЬЕ ПО ФОТО ПОЛКИ</b>",
        f"📍 <i>{overview}</i>\n",
        f"🥇 <b>#1 ТОП ВЫБОР (БРАТЬ ОБЯЗАТЕЛЬНО):</b>",
        f"   <b>{html.escape(str(top.get('name', 'Напиток')))}</b>",
        f"   🏷 Стиль: <b>{html.escape(str(top.get('style_type', '')))}</b>",
        f"   ⭐️ Рейтинг: <b>{html.escape(str(top.get('rating', '4.0/5.0')))}</b>",
        f"   💡 <i>Почему именно он:</i> {html.escape(str(top.get('why_choose', '')))}",
        f"   👅 <i>Вкусовой профиль:</i> {html.escape(str(top.get('taste_profile', '')))}",
        f"   🧀 <i>Идеальная закуска:</i> {html.escape(str(top.get('ideal_snack', '')))}\n"
    ]

    if safe and safe.get("name"):
        lines.append("🥈 <b>#2 НАДЕЖНАЯ КЛАССИКА (ПОСПОКОЙНЕЕ):</b>")
        lines.append(f"   <b>{html.escape(str(safe.get('name')))}</b> ({html.escape(str(safe.get('rating', '')))})")
        lines.append(f"   <i>{html.escape(str(safe.get('reason', '')))}</i>\n")

    if wild and wild.get("name"):
        lines.append("🥉 <b>#3 ЯРКИЙ ЭКСПЕРИМЕНТ (НЕОБЫЧНЫЙ ВКУС):</b>")
        lines.append(f"   <b>{html.escape(str(wild.get('name')))}</b> ({html.escape(str(wild.get('rating', '')))})")
        lines.append(f"   <i>{html.escape(str(wild.get('reason', '')))}</i>\n")

    if avoid:
        lines.append("🚫 <b>ЧТО НА ЭТОЙ ПОЛКЕ ЛУЧШЕ ПРОПУСТИТЬ:</b>")
        for av in avoid:
            lines.append(f"   • {html.escape(str(av))}")
        lines.append("")

    if hangover:
        risk = html.escape(str(hangover.get("risk_level", "Умеренный")))
        adv = html.escape(str(hangover.get("advice", "Пейте воду!")))
        lines.append(f"🤕 <b>Утренний прогноз:</b> {risk}")
        lines.append(f"   💡 <i>{adv}</i>\n")

    lines.append("<i>💡 Сделайте еще фото другой полки или напишите уточнение («что-нибудь кислое», «дешевле 200р», «под стейк») прямо сейчас!</i>")
    return "\n".join(lines)
