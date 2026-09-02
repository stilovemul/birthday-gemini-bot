import re
import json
import logging
from typing import Dict, Any, List, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("ShashlikCalc")


async def calculate_shashlik_marinade(
    user_id: int,
    meat_type: str = "Свиная шея",
    weight_kg: float = 2.0,
    style: str = "классический луковый",
    seen_titles: Optional[List[str]] = None
) -> Dict[str, Any]:
    onion_g = int(weight_kg * 400)
    salt_g = int(weight_kg * 11)
    pepper_g = int(weight_kg * 3)
    coriander_g = int(weight_kg * 2)
    paprika_g = int(weight_kg * 4)

    anti_repeat = ""
    if seen_titles:
        anti_repeat = f"\nВАЖНО: Пользователь уже мариновал: {', '.join(seen_titles[-10:])}. Предложи другой авторский стиль маринада или специй!"

    prompt = (
        "Ты признанный мастер мангала и шашлыка. Рассчитай точнейшие пропорции маринада и технологию жарки.\n"
        f"Тип мяса: {meat_type}. Вес: {weight_kg} кг. Стиль маринада: {style}.{anti_repeat}\n\n"
        "Сформируй расчет ингредиентов строго по граммам на указанный вес, время маринования, количество углей и секреты сочности БЕЗ уксуса.\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        f'  "title": "🍢 Маринад для шашлыка из {meat_type} ({weight_kg} кг)",\n'
        '  "marinade_time": "4-6 часов (или на ночь в холодильнике)",\n'
        '  "coals_needed": "1 большой мешок березовых углей (2.5-3 кг)",\n'
        '  "proportions": [\n'
        f'    "Мясо ({meat_type}) — {weight_kg} кг",\n'
        f'    "Репчатый лук — {onion_g}г (половину нарезать кольцами, половину натереть/пробить блендером для сока)",\n'
        f'    "Соль крупная (морская/каменная) — {salt_g}г (строго 10-12г на 1 кг мяса)",\n'
        f'    "Свежемолотый черный перец — {pepper_g}г",\n'
        f'    "Кориандр молотый — {coriander_g}г",\n'
        f'    "Паприка сладкая/копченая — {paprika_g}г",\n'
        '    "Газированная минеральная вода (сильногазированная) — 150-200 мл"\n'
        '  ],\n'
        '  "steps": [\n'
        '    "1. Нарежьте мясо одинаковыми кусками размером примерно 4-5 см поперек волокон.",\n'
        '    "2. Лук измельчите до кашицы, смешайте со специями и солью, вымесите мясо руками 5-7 минут как тесто, чтобы оно впитало весь луковый сок.",\n'
        '    "3. Залейте минералкой, накройте тарелкой под легкий гнет и отправьте в холод.",\n'
        '    "4. Жарьте на седых углях (без открытого пламени), часто переворачивая (каждые 40-60 сек) для сохранения соков внутри."\n'
        '  ],\n'
        '  "grill_secrets": "🔥 Главный секрет — луковый сок естественным образом размягчает волокна мяса лучше любого уксуса, делая его тающим во рту!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing shashlik JSON: {e}")

    return {
        "title": f"🍢 Шашлык из {meat_type} ({weight_kg} кг)",
        "marinade_time": "4-6 часов",
        "coals_needed": "2.5 кг березового угля",
        "proportions": [
            f"Мясо — {weight_kg} кг",
            f"Лук репчатый — {onion_g}г",
            f"Соль — {salt_g}г",
            "Специи (перец, паприка, кориандр)",
            "Минералка с газом — 150 мл"
        ],
        "steps": [
            "Нарезать мясо кусками 4-5 см",
            "Отжать луковый сок со специями и солью в мясо",
            "Вымесить 5 минут и мариновать 4 часа",
            "Жарить на седых углях, часто переворачивая"
        ],
        "grill_secrets": "Жарьте на седых углях без открытого огня!"
    }
