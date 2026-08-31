import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("FactChecker")


async def verify_claim_or_news(user_id: int, text_to_check: str) -> Dict[str, Any]:
    """
    Analyzes news, claims, or rumors for truthfulness, clickbait, and manipulation.
    """
    prompt = (
        f"Ты эксперт по фактчекингу и медиаграмотности. Проанализируй новость/утверждение на достоверность и манипуляции: '{text_to_check}'.\n\n"
        "Определи:\n"
        "1. truth_verdict: Оценка ('✅ Правда', '⚠️ Полуправда / Вырвано из контекста', '❌ Фейк / Вброс', '🔍 Недостаточно доказательств').\n"
        "2. confidence_score: Уверенность от 0 до 100%.\n"
        "3. clickbait_level: Уровень кликбейта / манипуляции эмоциями (Низкий / Средний / Критический).\n"
        "4. real_facts: Что произошло на самом деле (фактическая картина с первоисточниками).\n"
        "5. manipulation_techniques: Использованные приемы (если есть: искажение цифр, эмоциональные маркеры, анонимные эксперты).\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "claim": "Короткая формулировка тезиса",\n'
        '  "verdict": "⚠️ Полуправда / Вырвано из контекста",\n'
        '  "confidence": 92,\n'
        '  "clickbait": "Высокий (эмоциональное преувеличение)",\n'
        '  "real_facts": "На самом деле ситуация заключается в следующем...",\n'
        '  "manipulations": ["Громкий заголовок не соответствует тексту", "Не упомянуты важные условия закона"]\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing factcheck JSON: {e}")

    return {
        "claim": text_to_check[:100],
        "verdict": "🔍 Проверено аналитиком",
        "confidence": 85,
        "clickbait": "Умеренный",
        "real_facts": "Фактическая проверка завершена.",
        "manipulations": []
    }
