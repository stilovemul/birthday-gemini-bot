import re
import json
import logging
from typing import Dict, Any, Optional, List
from core.gemini import ask_gemini

logger = logging.getLogger("CraftBeerGuide")


async def get_craft_beer_guide(
    user_id: int,
    query: str = "",
    image_bytes: Optional[bytes] = None,
    seen_titles: Optional[List[str]] = None
) -> Dict[str, Any]:
    b_query = query if query else "Популярный крафтовый сорт (например: Zagovor, AF Brew, Jaws, Salden's, Guinness)"
    anti_repeat = ""
    if seen_titles:
        anti_repeat = f"\nВАЖНО: Пользователь уже исследовал следующие сорта: {', '.join(seen_titles[-10:])}. Предложи ДРУГОЙ уникальный сорт!"
    
    prompt = (
        "Ты профессиональный сертифицированный пивной сомелье (Master Cicerone) и эксперт по крафтовому и классическому пиву.\n"
        f"Запрос пользователя / название: '{b_query}'.{anti_repeat}\n\n"
        "Проанализируй сорт, оценки пивного сообщества (Untappd / RateBeer / отзывы энтузиастов) и дай исчерпывающий вердикт:\n"
        "1. Название пива, пивоварня и стиль (IPA, DIPA, NEIPA, Stout, Gose, Sour, Pilsner, Blanche, Lager, Porter и т.д.).\n"
        "2. Характеристики: Крепость (ABV), Горечь (IBU), плотность (Plato).\n"
        "3. Рейтинг сообщества (Untappd score / 5.0) и честное резюме отзывов: ВКУСНОЕ ИЛИ НЕТ? Плюсы и минусы.\n"
        "4. Вердикт сомелье: СТОИТ ЛИ ПОКУПАТЬ? (Брать обязательно / На любителя / Лучше пройти мимо).\n"
        "5. Идеальные закуски (Food Pairing):\n"
        "   - 🍞 Сухарики/гренки (какие именно идеально гармонируют)\n"
        "   - 🐟 Рыбка/морепродукты (какая рыба подчеркнет вкус, а какая испортит)\n"
        "   - 🥔 Чипсы/снеки\n"
        "   - 🍔 Горячие блюда/сыры\n"
        "6. БУДЕТ ЛИ УТРОМ БОЛЕТЬ ГОЛОВА? (Похмельный фактор: уровень риска, почему, и лайфхак как пить без тяжелого утра).\n"
        "7. Вкусовой профиль и ноты аромата (flavor_notes): СТРОГО НА РУССКОМ ЯЗЫКЕ (например: 'сочное спелое манго, маракуйя, цитрусовая цедра, сосновая хвоя' — обязательно переводи все английские термины вроде citrus, pine, resin, floral, malt, hops, tropical на сочный русский язык).\n"
        "8. ВСЕ поля JSON (включая закуски и вердикт) должны быть ТОЛЬКО НА КРАСИВОМ И ПОНЯТНОМ РУССКОМ ЯЗЫКЕ.\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "beer_name": "🍺 Zagovor - Decontrol (Double IPA)",\n'
        '  "brewery": "Zagovor Brewery",\n'
        '  "style": "Double New England IPA (DIPA)",\n'
        '  "abv": "8.0%",\n'
        '  "ibu": "45 IBU",\n'
        '  "untappd_rating": "4.15 / 5.0 ⭐️ (Топовый крафтовый рейтинг)",\n'
        '  "taste_verdict": "🔥 ВКУСНОЕ: Мощный тропический сок с мягким телом, нотки манго, персика и цитрусов. Спирт отлично скрыт, пьется легко.",\n'
        '  "buy_verdict": "✅ СТОИТ БРАТЬ: Эталонный представитель стиля, оправдывает каждую копейку.",\n'
        '  "snacks": {\n'
        '    "croutons": "Чесночные бородинские гренки со сливочным соусом",\n'
        '    "fish": "Слабосоленая форель или вяленый лосось (избегайте чересчур соленой воблы — она перебьет хмель)",\n'
        '    "chips": "Рифленые чипсы с паприкой или халапеньо",\n'
        '    "hot_food": "Сочный бургер с беконом, крылышки Баффало, сыр Чеддер"\n'
        '  },\n'
        '  "hangover_risk": {\n'
        '    "risk_level": "⚠️ Средне-высокий (при > 2 банок)",\n'
        '    "morning_forecast": "Крепость 8.0% и высокая плотность дают коварный эффект: пьется как сок, но 2-3 банки на утро дадут тяжелую голову из-за сахаров и градусов.",\n'
        '    "hangover_cure": "💡 Пейте 1 стакан воды на каждую банку и обязательно плотно поешьте перед дегустацией!"\n'
        '  },\n'
        '  "flavor_notes": "Спелое манго, маракуйя, цитрусовая цедра, сосновая смола",\n'
        '  "serving_temp": "8-10°C (бокал тюльпан или снифтер)"\n'
        "}"
    )

    if image_bytes:
        prompt_vision = (
            "Ты карманный пивной сомелье. Внимательно распознай пиво, этикетку, банку или кран на этом фото.\n"
            "Найди актуальную информацию и отзывы сообщества (Untappd) об этом сорте.\n"
            "Сформируй полный ответ в формате JSON со следующими полями: "
            "beer_name, brewery, style, abv, ibu, untappd_rating, taste_verdict (вкусное или нет), "
            "buy_verdict (стоит ли брать), snacks (croutons, fish, chips, hot_food), "
            "hangover_risk (risk_level, morning_forecast, hangover_cure), flavor_notes (НА РУССКОМ), serving_temp."
        )
        resp = await ask_gemini(user_id, prompt_vision, image_bytes=image_bytes)
    else:
        resp = await ask_gemini(user_id, prompt)

    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing craft beer JSON: {e}")

    return {
        "beer_name": "🍺 Zagovor Brewery - DIPA",
        "brewery": "Zagovor",
        "style": "New England DIPA",
        "abv": "8.0%",
        "ibu": "45 IBU",
        "untappd_rating": "4.15 / 5.0",
        "taste_verdict": "🔥 ВКУСНОЕ: Сочный тропический хмелевой сок, алкоголь отлично скрыт.",
        "buy_verdict": "✅ СТОИТ БРАТЬ: Один из лучших крафтовых сортов.",
        "snacks": {
            "croutons": "Чесночные бородинские гренки",
            "fish": "Вяленый лосось или кальмар",
            "chips": "Чипсы с паприкой",
            "hot_food": "Бургер или острые крылья"
        },
        "hangover_risk": {
            "risk_level": "Средний (при более 2 банок)",
            "morning_forecast": "Плотный эль требует умеренности.",
            "hangover_cure": "Пейте воду параллельно!"
        },
        "flavor_notes": "Манго, персик, грейпфрут, хвоя",
        "serving_temp": "8-10°C"
    }
