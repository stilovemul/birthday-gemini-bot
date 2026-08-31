import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("FineDisputer")


async def generate_fine_appeal(user_id: int, fine_details: str) -> Dict[str, Any]:
    """
    Analyzes traffic camera fine and generates official legal appeal template.
    """
    prompt = (
        f"Ты авто-юрист высшей категории. Составь юридически обоснованную жалобу на постановление о штрафе с камеры: '{fine_details}'.\n"
        "Типичные основания: ошибка распознавания номера, тень от машины пересекла сплошную, блик фар, машина продана по ДКП, за рулем был другой человек, знак скрыт ветками/снегом, вынужденный объезд препятствия.\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "violation_type": "Превышение скорости / Разметка / Тень",\n'
        '  "chances_percent": 85,\n'
        '  "grounds": "Недоказанность события правонарушения, техническая ошибка фиксации комплекса фотовидеофиксации (ст. 1.5, 24.5 КоАП РФ).",\n'
        '  "appeal_destination": "Начальнику ЦАФАП ГИБДД / В районный суд по месту фиксации",\n'
        '  "appeal_text": "ЖАЛОБА на постановление №... по делу об административном правонарушении... (готовый юридический текст)",\n'
        '  "deadline_days": 10,\n'
        '  "step_instruction": "Подайте жалобу в течение 10 суток с момента получения на Госуслугах через раздел Обжаловать или заказным письмом."\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing fine appeal JSON: {e}")

    return {
        "violation_type": "Штраф с камеры фотофиксации",
        "chances_percent": 70,
        "grounds": "Техническая ошибка камеры фиксации (ст. 1.5 КоАП РФ)",
        "appeal_destination": "ЦАФАП ГИБДД / Госуслуги",
        "appeal_text": "Жалоба на постановление об административном правонарушении...",
        "deadline_days": 10,
        "step_instruction": "Подайте через Госуслуги в течение 10 суток."
    }
