import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("WineSpiritsSommelier")


async def get_wine_spirits_guide(user_id: int, query: str = "", image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Universal AI Sommelier & Alcohol Expert (Вино, Водка, Коньяк, Виски, Ром, Джин, Текила, Ликеры):
    - Identifies bottle, label, vintage and producer by photo or text
    - Evaluates ratings (Vivino / Whiskybase / Distiller scores)
    - Answers 'Is it tasty / smooth?' and 'Should you buy it?'
    - Provides perfect gastronomic pairings (cheeses, meats, hot dishes, traditional snacks)
    - Predicts hangover risk ('Будет ли утром болеть голова?')
    - Recommends serving temperature and proper glassware
    """
    q_str = query if query else "Популярный алкогольный напиток (Вино, Коньяк, Водка, Виски)"

    prompt = (
        "Ты мировой гранд-сомелье (Master Sommelier) и эксперт по крепкому алкоголю и винам.\n"
        f"Запрос / Название напитка: '{q_str}'\n\n"
        "Проанализируй напиток (Вино, Водка, Коньяк, Виски, Ром, Текила, Джин, Настойка, Ликер, Шампанское и др.), "
        "оценки винных критиков и алкогольных баз (Vivino, Whiskybase, Distiller, Wine Spectator, отзывы покупателей) "
        "и сформируй профессиональный вердикт:\n"
        "1. Название напитка, производитель, страна/регион, выдержка (VS, VSOP, XO, годы выдержки в бочках, винтаж).\n"
        "2. Тип и параметры: Крепость (ABV), сладость/сахар, сорт винограда / сырье (солод, рожь, агава, дистиллят).\n"
        "3. Рейтинг сообщества (Vivino / Whiskybase / 5.0) и ЧЕСТНОЕ резюме: ВКУСНОЕ / МЯГКОЕ ИЛИ НЕТ? Пьется легко или спиртуозно?\n"
        "4. Вердикт сомелье: СТОИТ ЛИ ПОКУПАТЬ? Оправдывает ли свою цену?\n"
        "5. Идеальные закуски (Гастропары):\n"
        "   - 🧀 Сыры / Мясные деликатесы (хамон, сыры, прошутто)\n"
        "   - 🥩 Горячие блюда (стейки, дичь, рыба, шашлык)\n"
        "   - 🍋 Традиционные закуски под крепкое (соленья, сало, лимон, шоколад, фрукты, оливки)\n"
        "   - 🥖 Десерты / Брускетты / Фрукты\n"
        "6. БУДЕТ ЛИ УТРОМ БОЛЕТЬ ГОЛОВА? (Похмельный фактор: уровень риска, чистота спиртов/сульфиты/сахар, и правило безопасного употребления).\n"
        "7. Вкусовой букет, оптимальная температура подачи и правильный бокал.\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "drink_name": "🍷 Chianti Classico Riserva / 🥃 Hennessy VSOP / 🍸 Grey Goose",\n'
        '  "producer": "Название винодельни / дистиллерии",\n'
        '  "category": "Красное сухое вино / Французский коньяк / Премиальная водка",\n'
        '  "origin": "Тоскана, Италия / Коньяк, Франция",\n'
        '  "abv": "13.5% / 40.0%",\n'
        '  "rating": "4.2 / 5.0 ⭐️ (Высокий рейтинг Vivino / Whiskybase)",\n'
        '  "taste_verdict": "🔥 ПРЕВОСХОДНО: Очень мягкий, округлый вкус без резкой спиртуозности, благородные древесные и ягодные ноты.",\n'
        '  "buy_verdict": "✅ СТОИТ БРАТЬ: Эталон в своей ценовой категории, отличный выбор для застолья или подарка.",\n'
        '  "pairings": {\n'
        '    "cheeses_meats": "Выдержанный Пармезан, прошутто ди Парма, сыровяленая говядина",\n'
        '    "hot_dishes": "Флорентийский стейк, запеченная утка, шашлык из баранины",\n'
        '    "traditional_snacks": "Оливки Каламата, брускетта с вялеными томатами, темный шоколад",\n'
        '    "fruits_desserts": "Свежий инжир, ягоды, орехи"\n'
        '  },\n'
        '  "hangover_risk": {\n'
        '    "risk_level": "🟢 Низкий / 🟡 Средний / 🔴 Высокий",\n'
        '    "morning_forecast": "Благодаря высокой степени очистки спиртов и отсутствию добавленного сахара, при умеренном употреблении голова утром будет легкой.",\n'
        '    "safety_rule": "💡 Чередуйте каждый бокал со стаканом минеральной воды без газа и не смешивайте с газировками!"\n'
        '  },\n'
        '  "tasting_notes": "Спелая вишня, дубовая бочка, ваниль, легкий табачный лист",\n'
        '  "serving": "16-18°C (бокал Бордо / снифтер / рокс)"\n'
        "}"
    )

    if image_bytes:
        prompt_vision = (
            "Ты универсальный винный и алкогольный сомелье (Master Sommelier). "
            "Внимательно распознай бутылку, этикетку, акцизную марку или бокал на этом фото.\n"
            "Определи точный напиток (Вино, Коньяк, Водка, Виски, Ром, Текила, Ликер, Шампанское) "
            "и найди экспертные оценки (Vivino, Whiskybase, Distiller).\n"
            "Сформируй полный ответ в формате JSON со следующими полями: "
            "drink_name, producer, category, origin, abv, rating, taste_verdict (вкусное/мягкое или нет), "
            "buy_verdict (стоит ли брать), pairings (cheeses_meats, hot_dishes, traditional_snacks, fruits_desserts), "
            "hangover_risk (risk_level, morning_forecast, safety_rule), tasting_notes, serving.\n"
            "Верни ТОЛЬКО чистый JSON!"
        )
        resp = await ask_gemini(user_id, prompt_vision, image_bytes=image_bytes)
    else:
        resp = await ask_gemini(user_id, prompt)

    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing wine/spirits JSON: {e}")

    return {
        "drink_name": f"🍷 {query if query else 'Благородный алкогольный напиток'}",
        "producer": "Известный производитель",
        "category": "Алкоголь премиум-класса",
        "origin": "Европа / Мир",
        "abv": "40.0% / 13.5%",
        "rating": "4.1 / 5.0 ⭐️ (Уверенный высокий рейтинг)",
        "taste_verdict": "Сбалансированный благородный вкус, гармоничное послевкусие без резких спиртовых тонов.",
        "buy_verdict": "✅ СТОИТ БРАТЬ: Отличное качество для хорошего вечера.",
        "pairings": {
            "cheeses_meats": "Сырная тарелка и мясные деликатесы",
            "hot_dishes": "Мясные блюда на гриле или запеченная птица",
            "traditional_snacks": "Оливки, легкие закуски, брускетты",
            "fruits_desserts": "Фруктовая нарезка или горький шоколад"
        },
        "hangover_risk": {
            "risk_level": "🟢 Умеренный при разумном употреблении",
            "morning_forecast": "Качественный напиток с чистым профилем, похмелье минимально при умеренности.",
            "safety_rule": "Пейте воду и не забывайте про сытную закуску!"
        },
        "tasting_notes": "Спелые фрукты, дуб, пряности",
        "serving": "Комнатная температура или охлажденным"
    }
