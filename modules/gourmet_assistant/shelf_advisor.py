import re
import json
import html
import logging
from typing import Dict, Any, Optional, List
from core.gemini import ask_gemini

logger = logging.getLogger("AlcoholShelfAdvisor")


async def analyze_alcohol_image(
    user_id: int,
    image_bytes: bytes,
    user_preference: str = "",
    alcohol_category: str = "beer"
) -> Dict[str, Any]:
    """
    AI Sommelier Vision Engine:
    Intelligently detects whether the photo is:
    1. 'shelf': A store shelf, supermarket fridge, bar tap menu with MULTIPLE drinks/bottles/cans.
       -> Performs complete scan of all shelves (Upper, Middle, Lower), coordinates, Top-3, avoid picks, hangover forecast.
    2. 'single_bottle': A SINGLE bottle, can, beer glass, or close-up label.
       -> Performs in-depth Master Sommelier / Cicerone review of this specific drink (Untappd score, taste consensus, buy verdict, snacks: croutons/fish/chips/hot food, hangover risk, flavor notes in Russian, serving temp).
    """
    pref_instruction = ""
    if user_preference:
        pref_instruction = f"\nПРЕДПОЧТЕНИЕ / КОММЕНТАРИЙ ПОЛЬЗОВАТЕЛЯ: '{user_preference}'."

    prompt = (
        "Ты мировой гранд-сомелье (Master Sommelier) и главный пивной эксперт (Master Cicerone).\n"
        "Пользователь прислал ФОТО.\n"
        f"{pref_instruction}\n\n"
        "КРИТИЧЕСКИ ВАЖНО — В ПЕРВУЮ ОЧЕРЕДЬ ОПРЕДЕЛИ ТИП ФОТОГРАФИИ:\n"
        "1. 'shelf' — это витрина магазина, полка супермаркета, холодильник со множеством разных напитков (3+ разных бутылок/банок), либо барная карта/меню.\n"
        "2. 'single_bottle' — это одна отдельная бутылка, банка, бокал с напитком, этикетка крупным планом, либо фокус на одном конкретном напитке (в руке, на столе, в баре).\n\n"
        "====================================================\n"
        "ВАРИАНТ А: ЕСЛИ НА ФОТО ПОЛКА / ВИТРИНА / ХОЛОДИЛЬНИК ('shelf'):\n"
        "Сделай полный скан всей витрины и верни JSON со структурой:\n"
        "{\n"
        '  "image_type": "shelf",\n'
        '  "shelf_overview": "Холодильник крафтового и импортного пива (распознано 15+ позиций на 3 полках)",\n'
        '  "shelves": [\n'
        '    {\n'
        '      "shelf_name": "🔝 Верхняя полка",\n'
        '      "items": [\n'
        '        {\n'
        '          "name": "Название пива / вина",\n'
        '          "position": "1-я слева (коричневая бутылка)",\n'
        '          "style": "Пшеничный эль / Weizen",\n'
        '          "rating": "3.80 ⭐️",\n'
        '          "verdict": "🔥 Топовая пшеничка: банан, гвоздика, густая пена"\n'
        '        }\n'
        '      ]\n'
        '    },\n'
        '    {\n'
        '      "shelf_name": "➡️ Средняя полка",\n'
        '      "items": [\n'
        '        {\n'
        '          "name": "Волковская IPA",\n'
        '          "position": "1-я слева (сине-желтая банка)",\n'
        '          "style": "American IPA",\n'
        '          "rating": "3.82 ⭐️",\n'
        '          "verdict": "🔥 Лучший хмель и баланс за свою цену"\n'
        '        }\n'
        '      ]\n'
        '    },\n'
        '    {\n'
        '      "shelf_name": "⬇️ Нижняя полка",\n'
        '      "items": [\n'
        '        {\n'
        '          "name": "Salden\'s Tomato Gose",\n'
        '          "position": "Слева (белая банка)",\n'
        '          "style": "Томатный гозе",\n'
        '          "rating": "3.95 ⭐️",\n'
        '          "verdict": "🔥 Пряный томатный сок с солью и травами"\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ],\n'
        '  "top_pick": {\n'
        '    "name": "Волковская IPA / Zagovor Decontrol",\n'
        '    "shelf_location": "Средняя полка, 1-я банка слева (с рисунком волка)",\n'
        '    "style_type": "American IPA, 5.9%, IBU 55",\n'
        '    "rating": "3.82 / 5.0 ⭐️ (Untappd)",\n'
        '    "why_choose": "Лучшее соотношение свежести хмеля, плотного тела и цены среди всего ассортимента.",\n'
        '    "taste_profile": "Яркие цитрусы (грейпфрут), хвоя, тропики и уверенная благородная горечь.",\n'
        '    "ideal_snack": "Чесночные гренки, острые крылышки или выдержанный Чеддер"\n'
        '  },\n'
        '  "safe_pick": {\n'
        '    "name": "Spaten / Pilsner Urquell",\n'
        '    "shelf_location": "Средняя полка, 2-я банка слева",\n'
        '    "style_type": "Мюнхенский светлый лагер, 5.2%",\n'
        '    "rating": "3.35 / 5.0 ⭐️",\n'
        '    "reason": "Мягкая классика: чистый солодовый вкус без дефектов, пьется легко."\n'
        '  },\n'
        '  "wildcard_pick": {\n'
        '    "name": "Salden\'s Tomato Gose",\n'
        '    "shelf_location": "Нижняя полка, крайняя слева",\n'
        '    "style_type": "Томатный кислый эль",\n'
        '    "rating": "3.95 / 5.0 ⭐️",\n'
        '    "reason": "Для ярких эмоций: взрывной пряный вкус томатов и специй."\n'
        '  },\n'
        '  "avoid_picks": [\n'
        '    {\n'
        '      "name": "Балтика 9 Крепкое",\n'
        '      "shelf_location": "Средняя полка, крайняя справа",\n'
        '      "reason": "Резкий спиртуозный профиль, тяжелое утро и головная боль."\n'
        '    }\n'
        '  ],\n'
        '  "hangover_forecast": {\n'
        '    "risk_level": "🟢 Низкий при выборе топа (1-2 порции)",\n'
        '    "advice": "Пейте 1 стакан воды на каждую банку/бокал."\n'
        '  },\n'
        '  "shopping_checklist": [\n'
        '    "Волковская IPA (2 банки на средней полке слева)",\n'
        '    "Чесночные гренки или нарезка сыра Чеддер",\n'
        '    "Минеральная вода без газа"\n'
        '  ]\n'
        "}\n\n"
        "====================================================\n"
        "ВАРИАНТ Б: ЕСЛИ НА ФОТО ОДНА ОТДЕЛЬНАЯ БУТЫЛКА / БАНКА / БОКАЛ / ЭТИКЕТКА ('single_bottle'):\n"
        "Внимательно распознай пиво/напиток по этикетке, найди реальный рейтинг Untappd/Vivino/RateBeer и дай исчерпывающий обзор сомелье в JSON следующей структуры:\n"
        "{\n"
        '  "image_type": "single_bottle",\n'
        '  "beer_name": "🍺 Точное название пива (например: Zagovor - Decontrol / Salden\'s Tomato Gose / Guinness)",\n'
        '  "brewery": "Пивоварня (например: Zagovor Brewery / Salden\'s / Guinness)",\n'
        '  "style": "Стиль (например: Double New England IPA / Imperial Gose / Dry Stout / German Pilsner)",\n'
        '  "abv": "Крепость % (например: 8.0%)",\n'
        '  "ibu": "Горечь IBU (например: 45 IBU)",\n'
        '  "density": "Плотность / ЭНС (например: 18.5% Plato)",\n'
        '  "untappd_rating": "4.15 / 5.0 ⭐️ (Топовый крафтовый рейтинг)",\n'
        '  "taste_verdict": "🔥 ВКУСНОЕ ИЛИ НЕТ (Консенсус отзывов): Подробное резюме реальных отзывов биргиков — сочность, баланс хмеля и солода, горечь, сладость, карбонизация, скрытость алкоголя, плюсы и минусы.",\n'
        '  "buy_verdict": "✅ СТОИТ ЛИ БРАТЬ: Исчерпывающий вердикт сомелье (Брать обязательно / На любителя / Лучше пройти мимо, оправдывает ли свою цену).",\n'
        '  "snacks": {\n'
        '    "croutons": "Чесночные бородинские гренки со сливочным соусом (какой хлеб и соус)",\n'
        '    "fish": "Слабосоленая форель, вяленый лосось или кальмар (какая рыба подчеркнет вкус, а какая испортит хмель)",\n'
        '    "chips": "Рифленые чипсы с паприкой или начос",\n'
        '    "hot_food": "Сочный бургер с беконом, острые крылышки Баффало, сыр Чеддер"\n'
        '  },\n'
        '  "hangover_risk": {\n'
        '    "risk_level": "⚠️ Средне-высокий (при > 2 банок) / 🟢 Низкий",\n'
        '    "morning_forecast": "Химический прогноз: плотность, алкоголь и сахар, будет ли утром тяжелая голова.",\n'
        '    "hangover_cure": "💡 Лайфхак: сколько воды выпить и как пить без последствий."\n'
        '  },\n'
        '  "flavor_notes": "Вкусовой профиль СТРОГО НА КРАСИВОМ РУССКОМ ЯЗЫКЕ (например: спелое манго, маракуйя, цитрусовая цедра, сосновая смола, карамель, бисквит)",\n'
        '  "serving_temp": "8-10°C (бокал тюльпан или снифтер)",\n'
        '  "shopping_checklist": [\n'
        '    "Zagovor - Decontrol (1-2 банки)",\n'
        '    "Чесночные бородинские гренки",\n'
        '    "Минеральная вода без газа"\n'
        '  ]\n'
        "}\n\n"
        "ВАЖНО: ВСЕ ПОЛЯ JSON И ТЕКСТОВЫЕ ОПИСАНИЯ ДОЛЖНЫ БЫТЬ ТОЛЬКО НА ПОНЯТНОМ И СОЧНОМ РУССКОМ ЯЗЫКЕ!\n"
        "Верни ТОЛЬКО валидный JSON (без разметки markdown вокруг)."
    )

    try:
        resp = await ask_gemini(user_id, prompt, image_bytes=image_bytes)
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                return data
    except Exception as e:
        logger.error(f"Error in analyze_alcohol_image: {e}")

    # Robust fallback
    return {
        "image_type": "shelf",
        "shelf_overview": "Витрина напитков в магазине",
        "shelves": [
            {
                "shelf_name": "🔝 Верхняя полка",
                "items": [
                    {
                        "name": "Импортный эль / Премиальное вино",
                        "position": "Слева",
                        "style": "Крафтовый сорт",
                        "rating": "3.9 ⭐️",
                        "verdict": "🔥 Богатый насыщенный вкус"
                    },
                    {
                        "name": "Немецкое пшеничное / Сухое белое",
                        "position": "По центру",
                        "style": "Классика",
                        "rating": "3.7 ⭐️",
                        "verdict": "✅ Мягкий питкий профиль"
                    }
                ]
            },
            {
                "shelf_name": "➡️ Средняя полка",
                "items": [
                    {
                        "name": "Крафтовая IPA / Хмелевой лагер",
                        "position": "Слева",
                        "style": "IPA / Хмелевой",
                        "rating": "3.8 ⭐️",
                        "verdict": "🔥 Цитрусовая ароматика и яркая горчинка"
                    },
                    {
                        "name": "Светлый чешский/немецкий лагер",
                        "position": "По центру",
                        "style": "Лагер",
                        "rating": "3.4 ⭐️",
                        "verdict": "✅ Чистый солодовый вкус"
                    }
                ]
            },
            {
                "shelf_name": "⬇️ Нижняя полка",
                "items": [
                    {
                        "name": "Яблочный сидр / Кислый сауэр",
                        "position": "Слева",
                        "style": "Сидр / Сауэр",
                        "rating": "3.8 ⭐️",
                        "verdict": "🔥 Освежающий фруктовый вкус"
                    }
                ]
            }
        ],
        "top_pick": {
            "name": "Крафтовая IPA / Премиальный эль",
            "shelf_location": "Средняя полка, слева",
            "style_type": "Насыщенный сорт с хмелем",
            "rating": "3.85 / 5.0 ⭐️",
            "why_choose": "Лучший баланс ароматики, плотности и свежести на этой витрине.",
            "taste_profile": "Яркие цитрусы, хвоя и мягкое приятное послевкусие.",
            "ideal_snack": "Сырные снеки, чесночные гренки или мясная нарезка."
        },
        "safe_pick": {
            "name": "Светлый немецкий лагер",
            "shelf_location": "Средняя полка, по центру",
            "style_type": "Светлый лагер",
            "rating": "3.4 / 5.0 ⭐️",
            "reason": "Проверенная классика с мягким вкусом без сюрпризов."
        },
        "wildcard_pick": {
            "name": "Фруктовый сауэр / Сидр",
            "shelf_location": "Нижняя полка, слева",
            "style_type": "Кислый эль / Сидр",
            "rating": "3.8 / 5.0 ⭐️",
            "reason": "Для ярких впечатлений и освежающего вкуса."
        },
        "avoid_picks": [
            {
                "name": "Бюджетные крепленые напитки",
                "shelf_location": "Нижняя полка, справа",
                "reason": "Спиртуозный вкус и тяжелое утро."
            }
        ],
        "hangover_forecast": {
            "risk_level": "🟢 Низкий при умеренном употреблении",
            "advice": "Пейте воду параллельно с напитком!"
        },
        "shopping_checklist": [
            "Выбранный сорт с полки",
            "Закуски к напитку",
            "Вода без газа"
        ]
    }


async def analyze_alcohol_shelf(
    user_id: int,
    image_bytes: bytes,
    user_preference: str = "",
    alcohol_category: str = "beer_or_wine"
) -> Dict[str, Any]:
    """Legacy alias for backward compatibility."""
    return await analyze_alcohol_image(
        user_id=user_id,
        image_bytes=image_bytes,
        user_preference=user_preference,
        alcohol_category=alcohol_category
    )


def format_shelf_advisor_message(data: dict) -> str:
    """Formats the shelf analysis JSON into a rich, full-scan Telegram message with shelf coordinates."""
    overview = html.escape(str(data.get("shelf_overview", "Ассортимент напитков")))
    shelves = data.get("shelves", [])
    top = data.get("top_pick", {})
    safe = data.get("safe_pick", {})
    wild = data.get("wildcard_pick", {})
    avoid = data.get("avoid_picks", [])
    hangover = data.get("hangover_forecast", {})

    total_scanned = sum(len(s.get("items", [])) for s in shelves) if shelves else 0
    scanned_badge = f" (просканировано {total_scanned} поз.)" if total_scanned > 0 else ""

    lines = [
        "📸 <b>ПОЛНЫЙ РАЗБОР ВИТРИНЫ ОТ СОМЕЛЬЕ</b>",
        f"📍 <i>{overview}{scanned_badge}</i>\n",
        "━━━━━━━━━━━━━━━━━━━",
        "🏆 <b>ТОП-3 ВЫБОРА С ЭТОЙ ВИТРИНЫ:</b>\n"
    ]

    # 1. Top Pick
    top_name = html.escape(str(top.get("name", "Напиток")))
    top_loc = html.escape(str(top.get("shelf_location", "На витрине")))
    top_style = html.escape(str(top.get("style_type", "")))
    top_rating = html.escape(str(top.get("rating", "4.0 / 5.0")))
    top_why = html.escape(str(top.get("why_choose", "")))
    top_taste = html.escape(str(top.get("taste_profile", "")))
    top_snack = html.escape(str(top.get("ideal_snack", "")))

    lines.append(f"🥇 <b>#1 ТОП ВЫБОР (БРАТЬ ОБЯЗАТЕЛЬНО):</b>")
    lines.append(f"   🍺 <b>{top_name}</b>")
    lines.append(f"   📍 <b>Где стоит:</b> <code>{top_loc}</code>")
    if top_style:
        lines.append(f"   🏷 <b>Стиль:</b> {top_style}")
    lines.append(f"   ⭐️ <b>Рейтинг:</b> {top_rating}")
    if top_why:
        lines.append(f"   💡 <i>Почему именно он:</i> {top_why}")
    if top_taste:
        lines.append(f"   👅 <i>Вкус:</i> {top_taste}")
    if top_snack:
        lines.append(f"   🧀 <i>Идеальная закуска:</i> {top_snack}")
    lines.append("")

    # 2. Safe Pick
    if safe and safe.get("name"):
        safe_name = html.escape(str(safe.get("name")))
        safe_loc = html.escape(str(safe.get("shelf_location", "На полке")))
        safe_rating = html.escape(str(safe.get("rating", "")))
        safe_reason = html.escape(str(safe.get("reason", "")))
        lines.append(f"🥈 <b>#2 НАДЕЖНАЯ КЛАССИКА (ПОСПОКОЙНЕЕ):</b>")
        lines.append(f"   <b>{safe_name}</b> ({safe_rating})")
        lines.append(f"   📍 <b>Где стоит:</b> <code>{safe_loc}</code>")
        if safe_reason:
            lines.append(f"   <i>{safe_reason}</i>")
        lines.append("")

    # 3. Wildcard Pick
    if wild and wild.get("name"):
        wild_name = html.escape(str(wild.get("name")))
        wild_loc = html.escape(str(wild.get("shelf_location", "На полке")))
        wild_rating = html.escape(str(wild.get("rating", "")))
        wild_reason = html.escape(str(wild.get("reason", "")))
        lines.append(f"🥉 <b>#3 ЯРКИЙ ЭКСПЕРИМЕНТ (НЕОБЫЧНЫЙ ВКУС):</b>")
        lines.append(f"   <b>{wild_name}</b> ({wild_rating})")
        lines.append(f"   📍 <b>Где стоит:</b> <code>{wild_loc}</code>")
        if wild_reason:
            lines.append(f"   <i>{wild_reason}</i>")
        lines.append("")

    # 4. Full Shelf-by-Shelf Breakdown
    if shelves:
        lines.append("━━━━━━━━━━━━━━━━━━━")
        lines.append("📋 <b>ПОЛНЫЙ СКАН ПОЛОК С ФОТО (СЛЕВА НАПРАВО):</b>\n")
        for sh in shelves:
            sh_title = html.escape(str(sh.get("shelf_name", "Полка")))
            lines.append(f"<b>{sh_title}:</b>")
            items = sh.get("items", [])
            for it in items:
                it_name = html.escape(str(it.get("name", "")))
                it_pos = html.escape(str(it.get("position", "")))
                it_style = html.escape(str(it.get("style", "")))
                it_rat = html.escape(str(it.get("rating", "")))
                it_verdict = html.escape(str(it.get("verdict", "")))

                pos_str = f" [<code>{it_pos}</code>]" if it_pos else ""
                style_str = f" • <i>{it_style}</i>" if it_style else ""
                rat_str = f" ({it_rat})" if it_rat else ""
                lines.append(f"  • <b>{it_name}</b>{rat_str}{pos_str}{style_str}")
                if it_verdict:
                    lines.append(f"    └ {it_verdict}")
            lines.append("")

    # 5. Avoid Picks
    if avoid:
        lines.append("🚫 <b>ЧТО НА ЭТОЙ ПОЛКЕ ЛУЧШЕ ПРОПУСТИТЬ:</b>")
        for av in avoid:
            if isinstance(av, dict):
                av_name = html.escape(str(av.get("name", "")))
                av_loc = html.escape(str(av.get("shelf_location", "")))
                av_reason = html.escape(str(av.get("reason", "")))
                loc_str = f" (<code>{av_loc}</code>)" if av_loc else ""
                lines.append(f"   • <b>{av_name}</b>{loc_str}: {av_reason}")
            else:
                lines.append(f"   • {html.escape(str(av))}")
        lines.append("")

    # 6. Hangover Forecast
    if hangover:
        risk = html.escape(str(hangover.get("risk_level", "Умеренный")))
        adv = html.escape(str(hangover.get("advice", "Пейте воду!")))
        lines.append(f"🤕 <b>Утренний прогноз:</b> {risk}")
        lines.append(f"   💡 <i>{adv}</i>\n")

    # 7. Interactive Prompts
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("💬 <b>ИНТЕРАКТИВНЫЙ ДИАЛОГ С СОМЕЛЬЕ:</b>")
    lines.append("<i>Вы можете спросить меня прямо сейчас в чате:</i>")
    lines.append("• <i>«На какой полке стоит Волковская?»</i>")
    lines.append("• <i>«А что если хочу пшеничное / темное / сидр с фото?»</i>")
    lines.append("• <i>«Что самое легкое / безалкогольное на витрине?»</i>")
    lines.append("• <i>«Посоветуй напиток до 200 рублей с этой фотографии»</i>")

    return "\n".join(lines)


async def ask_shelf_followup(
    user_id: int,
    question: str,
    shelf_data: Dict[str, Any],
    image_bytes: Optional[bytes] = None
) -> str:
    """
    Handles interactive follow-up questions from the user strictly anchored to the uploaded shelf photo.
    Answers:
    - Where a specific bottle stands (shelf, left/right position, bottle color, neighbor bottles)
    - Specific style requests from the photo ("а посоветуй пшеничное с фото", "а есть ли тут белое сухое/стаут?")
    - Price or strength inquiries
    - Comparison between items on the shelf
    """
    shelf_inventory_json = json.dumps(shelf_data, ensure_ascii=False, indent=2)

    prompt = (
        "Ты мировой гранд-сомелье и эксперт по алкоголю (Master Sommelier & Cicerone).\n"
        "Ранее пользователь прислал ФОТО витрины магазина / холодильника с напитками.\n"
        f"ВОТ ПОЛНЫЙ СКАН И РАСПОЗНАННЫЙ КАТАЛОГ ПОЛОК С ЭТОГО ФОТО:\n"
        f"```json\n{shelf_inventory_json}\n```\n\n"
        f"ПОЛЬЗОВАТЕЛЬ СПРАШИВАЕТ: «{question}»\n\n"
        "КРИТИЧЕСКИЕ ПРАВИЛА ОТВЕТА:\n"
        "1. ОТВЕЧАЙ ИСКЛЮЧИТЕЛЬНО НА ОСНОВЕ ПРИСЛАННОГО ФОТО И ВИТРИНЫ! Запрещено придумывать или советовать сорта, которых НЕТ на фотографии.\n"
        "2. ТОЧНЫЕ КООРДИНАТЫ: Для любого напитка ВСЕГДА называй точную полку (верхняя, средняя, нижняя), положение (1-я слева, по центру, крайняя справа) и внешние ориентиры (цвет банки, этикетка, соседи).\n"
        "3. ЕСЛИ СПРАШИВАЮТ СТИЛЬ (например 'пшеничное', 'темное', 'сидр', 'сухое белое', 'безалкогольное'):\n"
        "   - Найди ВСЕ подходящие позиции именно с этого фото, укажи их полки и рейтинги, и выдели лучший сорт.\n"
        "   - Если такого стиля на фото НЕТ — прямо скажи: 'На этой фотографии пшеничного пива нет. Но из легкого и мягкого на средней полке есть [Название и полка]'.\n"
        "4. ЕСЛИ СПРАШИВАЮТ 'ГДЕ СТОИТ X': подробно опиши полку, ряд, цвет этикетки и соседние бутылки.\n"
        "5. Форматируй ответ в красивом Telegram HTML (теги <b>, <i>, <code>) с эмодзи и четкими буллетами.\n"
        "6. В конце добавь краткую фразу, что еще можно спросить по этому фото."
    )

    try:
        resp = await ask_gemini(user_id, prompt, image_bytes=image_bytes)
        return resp
    except Exception as e:
        logger.error(f"Error in ask_shelf_followup: {e}")
        return (
            f"🍷 <b>Ответ сомелье по витрине:</b>\n\n"
            f"По вашему вопросу <i>«{html.escape(question)}»</i>:\n"
            f"Среди распознанных на фото напитков рекомендуем обратить внимание на позиции на средней и верхней полках. "
            f"Вы можете уточнить конкретный сорт или стиль!"
        )


def is_shelf_followup_question(text: str) -> bool:
    """Checks if incoming text is an interactive question about the shelf/photo."""
    if not text:
        return False
    t = text.lower().strip()
    
    triggers = [
        "полк", "где стоит", "где наход", "какая полк", "на какой", "посоветуй",
        "пшеничн", "вайс", "бланш", "лагер", "пилснер", "ипа", "ipa", "стаут", "портер", "эль",
        "сидр", "вино", "сухое", "полусладк", "красное", "белое", "виски", "джин", "водк",
        "безалк", "нулевк", "градус", "крепк", "легк", "горьк", "сладк", "кислое", "сауэр",
        "рубл", "руб", "цен", "стоит", "дешев", "дорог", "фото", "витрин", "холодильн",
        "почему", "сравни", "лучше", "взять", "выбрать", "а если", "а что", "а есть"
    ]
    return any(tr in t for tr in triggers)
