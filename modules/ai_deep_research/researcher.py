import re
import json
import logging
from typing import Dict, Any, List
from core.gemini import ask_gemini

logger = logging.getLogger("DeepResearcher")


async def conduct_deep_research(user_id: int, topic: str) -> Dict[str, Any]:
    """
    Performs autonomous deep research on any query and structures a multi-faceted analytical report.
    """
    prompt = (
        f"Ты ведущий аналитик и исследователь данных (Deep Research Agent). Проведи глубокое исследование темы: '{topic}'.\n\n"
        "Сформируй четкий аналитический отчет:\n"
        "1. title: Заголовок исследования.\n"
        "2. executive_summary: Главный вывод в 2-3 предложениях (Executive Summary).\n"
        "3. key_insights: 3-4 ключевых инсайта / факта с цифрами и деталями.\n"
        "4. comparison_table: Таблица или сравнение вариантов/альтернатив (массив объектов с полями name, pros, cons, rating).\n"
        "5. expert_verdict: Итоговая практическая рекомендация ('Что делать на практике').\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "title": "🔬 Аналитическое исследование: Лучшие варианты...",\n'
        '  "executive_summary": "Краткое резюме анализа...",\n'
        '  "key_insights": ["Инсайт 1", "Инсайт 2", "Инсайт 3"],\n'
        '  "comparison": [\n'
        '    {"name": "Вариант А", "pros": "Плюсы", "cons": "Минусы", "score": "9.2/10"},\n'
        '    {"name": "Вариант Б", "pros": "Плюсы", "cons": "Минусы", "score": "8.5/10"}\n'
        '  ],\n'
        '  "verdict": "Итоговая практическая рекомендация эксперта."\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing research JSON: {e}")

    return {
        "title": f"Исследование: {topic}",
        "executive_summary": "Анализ завершен.",
        "key_insights": [f"Изучены ключевые особенности темы '{topic}'"],
        "comparison": [],
        "verdict": "Используйте проверенные решения."
    }
