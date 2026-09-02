import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("ManipulationShield")


async def analyze_manipulation(user_id: int, text: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Deconstructs psychological manipulation, hidden aggression, and guilt-tripping in messages and screenshots.
    Provides 3 counter-response strategies.
    """
    prompt = (
        "Ты эксперт по психологии коммуникаций, профайлер и специалист по защите личных границ (Anti-Manipulation Shield).\n"
        f"Сообщение или переписка для анализа:\n<<<\n{text}\n>>>\n\n"
        "Выполни глубокий разбор:\n"
        "1. Уровень манипулятивности (0-100%) и статус (🔴 Опасная манипуляция / 🟡 Скрытое давление / 🟢 Конструктивный диалог).\n"
        "2. Выявленные тактики манипуляции (Газлайтинг, Навязывание чувства вины, Пассивная агрессия, Ложная срочность, Обесценивание, Давление авторитетом, Жертвенность, Двойные стандарты).\n"
        "3. Истинный мотив собеседника: ЧТО НА САМОМ ДЕЛЕ ОН ПЫТАЕТСЯ ПОЛУЧИТЬ или заставить вас почувствовать/сделать?\n"
        "4. Стратегия 1 (Дипломатичная): вежливый, но твердый ответ, сохраняющий отношения, но пресекающий манипуляцию.\n"
        "5. Стратегия 2 (Жесткий щит): холодный ответ, моментально закрывающий тему и ставящий железобетонные границы без оправданий.\n"
        "6. Стратегия 3 (Ироничная / Разрушающая сценарий): остроумный ответ, сбивающий спесь и возвращающий мяч манипулятору.\n\n"
        "Верни ответ СТРОГО в формате JSON:\n"
        "{\n"
        '  "manipulation_score": "80%",\n'
        '  "status_badge": "🔴 Скрытая манипуляция и давление на вину",\n'
        '  "tactics_detected": ["Навязывание чувства долга", "Обесценивание ваших усилий", "Пассивная агрессия"],\n'
        '  "hidden_agenda": "Собеседник пытается переложить ответственность и вынудить вас сделать работу за него под видом обиды.",\n'
        '  "diplomatic_reply": "Я понимаю твою позицию, однако в рамках договоренностей моя часть работы выполнена. Давай сосредоточимся на...",\n'
        '  "firm_shield_reply": "Я не готов принимать на свой счет эти претензии. Мое решение остается в силе.",\n'
        '  "witty_counter_reply": "Интересная попытка сделать меня виноватым, но давай лучше вернемся к фактам."\n'
        "}"
    )

    if image_bytes:
        prompt_vision = (
            "Ты эксперт по анализу манипуляций в переписке. Внимательно прочитай переписку на этом скриншоте.\n"
            "Выяви все скрытые манипуляции, пассивную агрессию, токсичность и давление.\n"
            "Сформируй полный ответ в JSON: manipulation_score, status_badge, tactics_detected (массив), "
            "hidden_agenda (истинный мотив), diplomatic_reply, firm_shield_reply, witty_counter_reply.\n"
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
        logger.error(f"Error parsing manipulation shield JSON: {e}")

    return {
        "manipulation_score": "60%",
        "status_badge": "🟡 Обнаружено скрытое давление",
        "tactics_detected": ["Попытка эмоционального давления"],
        "hidden_agenda": "Собеседник пытается сместить фокус внимания и навязать свои условия.",
        "diplomatic_reply": "Спасибо за обратную связь. Давайте придерживаться согласованного плана.",
        "firm_shield_reply": "Моя позиция остается неизменной. Продолжим в рабочем порядке.",
        "witty_counter_reply": "Давайте отложим эмоции в сторону и посмотрим на реальные цифры."
    }
