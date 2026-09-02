import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("Icebreakers")

ICEBREAKER_MODES = {
    "dating": {
        "title": "💘 Дейтинг & Знакомства",
        "description": "Tinder, Pure, VK Знакомства, соцсети — остроумные, цепляющие заходы без банальщины и кринжа."
    },
    "networking": {
        "title": "💼 Бизнес-Нетворкинг",
        "description": "LinkedIn, Telegram, конференции, поиск партнеров/клиентов/менторов — вежливо, статусно, с пользой."
    },
    "revive": {
        "title": "🔥 Оживление диалога",
        "description": "Когда собеседник замолчал или переписка угасла — органичные способы легко возобновить общение."
    },
    "creative": {
        "title": "🎭 Нестандартный креатив",
        "description": "Смелые, интригующие и юмористические фразы, ломающие шаблонные ожидания."
    }
}


async def generate_icebreakers(user_id: int, context: str, category: str = "dating", image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Generates non-cringe, high-conversion ice-breakers and opening lines for dating, business, and social networking.
    """
    cat_info = ICEBREAKER_MODES.get(category, ICEBREAKER_MODES["dating"])

    prompt = (
        "Ты мастер харизматичной коммуникации, эксперт по дейтингу и бизнес-нетворкингу.\n"
        f"Категория: {cat_info['title']} ({cat_info['description']})\n"
        f"Контекст профиля / ситуация / детали: '{context}'\n\n"
        "Сгенерируй 4 первоклассных открывающих сообщения (Ice-Breakers):\n"
        "- БЕЗ заезженных клише ('привет как дела', 'твоей маме зять не нужен').\n"
        "- С привязкой к деталям контекста (хобби, фото, работа, город, атмосфера).\n"
        "- Разные по тональности: 1) С легкой иронией, 2) Интригующий вопрос, 3) Наблюдательный комплимент, 4) Смелый крючок.\n"
        "- К каждому варианту добавь пояснение (Почему это сработает) и фразу для развития темы.\n\n"
        "Верни ответ СТРОГО в формате JSON:\n"
        "{\n"
        f'  "category_title": "{cat_info["title"]}",\n'
        '  "profile_insight": "Главный крючок, за который мы зацепились в описании",\n'
        '  "icebreakers": [\n'
        '    {\n'
        '      "line": "Текст первого сообщения",\n'
        '      "style": "Ироничный / Интригующий / Экспертный",\n'
        '      "why_it_works": "Почему вызовет улыбку и желание ответить",\n'
        '      "followup_hook": "Что написать следующим шагом после ответа"\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    if image_bytes:
        prompt_vision = (
            "Ты эксперт по харизматичным знакомствам. Посмотри на это фото/скриншот профиля.\n"
            "Найди интересные детали на фото (фон, одежда, эмоция, питомцы, путешествия) "
            "и составь 4 идеальных, остроумных первых сообщения для знакомства.\n"
            "Верни ответ в JSON: category_title, profile_insight, icebreakers (массив из 4 объектов: line, style, why_it_works, followup_hook).\n"
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
        logger.error(f"Error parsing icebreakers JSON: {e}")

    return {
        "category_title": cat_info["title"],
        "profile_insight": "Универсальный цепляющий заход на основе общих интересов.",
        "icebreakers": [
            {
                "line": "Кажется, у нас как минимум один общий повод для хорошей беседы. С чего начнем: с кофе или с разоблачения мифов?",
                "style": "Интригующий",
                "why_it_works": "Задает открытый выбор и легкую игровую динамику.",
                "followup_hook": "Развить тему любимых мест в городе."
            }
        ]
    }
