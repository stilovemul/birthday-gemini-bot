import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("CognitiveBiases")


async def analyze_cognitive_biases(user_id: int, situation: str) -> Dict[str, Any]:
    """
    Analyzes user dilemmas, conflicts, and decisions to detect cognitive biases and psychological traps.
    Provides a clear anti-bias checklist and rational action steps.
    """
    prompt = (
        "Ты мировой эксперт по рациональному мышлению, когнитивно-поведенческой психологии (CBT) и поведенческой экономике (в стиле Даниэля Канемана и Чарли Мангера).\n"
        f"Ситуация / рассуждение / дилемма пользователя:\n<<<\n{situation}\n>>>\n\n"
        "Выполни строгий аудит мышления:\n"
        "1. Определи главные когнитивные искажения (Cognitive Biases), в ловушку которых попадает человек в этой ситуации "
        "(например: Ошибка выжившего, Эффект невозвратных затрат / Sunk Cost, Ошибка подтверждения / Confirmation Bias, "
        "Фундаментальная ошибка атрибуции, Эффект Даннинга-Крюгера, Черно-белое мышление, Иллюзия контроля, Катастрофизация, Предвзятость статус-кво).\n"
        "2. Объясни простым и понятным языком: ПОЧЕМУ мозг в этой ситуации ошибается и какую эволюционную ловушку он захлопнул.\n"
        "3. Дай 'Рациональный аудит (Anti-Bias Checklist)' — 3 контрольных вопроса или факта, которые отрезвляют и показывают реальность без искажений.\n"
        "4. Сформулируй 1 конкретное, прагматичное действие / решение, свободное от этих иллюзий.\n\n"
        "Верни ответ СТРОГО в формате JSON:\n"
        "{\n"
        '  "detected_biases": [\n'
        '    {\n'
        '      "name": "Название искажения (например: Ошибка невозвратных затрат / Sunk Cost Fallacy)",\n'
        '      "description": "Краткое объяснение, как именно это искажение проявляется в вашей ситуации"\n'
        '    }\n'
        '  ],\n'
        '  "brain_trap_explanation": "Почему мозг обманывает себя в данном случае",\n'
        '  "rational_checklist": [\n'
        '    "Контрольный вопрос 1",\n'
        '    "Контрольный вопрос 2",\n'
        '    "Контрольный вопрос 3"\n'
        '  ],\n'
        '  "optimal_rational_step": "Четкий, трезвый план действий без иллюзий"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing cognitive biases JSON: {e}")

    return {
        "detected_biases": [
            {
                "name": "Эмоциональное обоснование",
                "description": "Принятие решений под влиянием сиюминутного эмоционального фона вместо анализа вероятностей."
            }
        ],
        "brain_trap_explanation": "Мозг стремится избежать дискомфорта и выбирает привычный шаблон.",
        "rational_checklist": [
            "Каковы объективные цифры и факты?",
            "Что бы вы посоветовали лучшему другу в такой же ситуации?",
            "Что самое худшее реально может произойти и как это решить?"
        ],
        "optimal_rational_step": "Взять паузу на 24 часа и оценить ситуацию по сухим фактам."
    }
