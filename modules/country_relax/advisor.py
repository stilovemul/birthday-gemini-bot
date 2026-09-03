import json
import logging
import re
from typing import Optional, Dict, Any, Tuple
from core.gemini import get_genai_client, CANDIDATE_MODELS
from modules.country_relax.storage import (
    get_last_country_resort,
    add_country_chat_turn,
    _memory_cache,
    _load_history
)

logger = logging.getLogger("CountryRelaxAdvisor")


def get_country_chat_history(user_id: int):
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return user_data.get("chat_history", [])


async def process_country_conversation(user_id: int, user_message: str) -> Tuple[bool, Optional[str]]:
    """
    Analyzes user message in the context of the currently viewed countryside resort / hotel / cottage club.
    Returns:
        (is_followup: bool, response_or_new_query: Optional[str])
        - If (True, answer_text): This was a question/discussion about the resort, answer_text is the formatted reply.
        - If (False, new_search_query): This was a request for a brand new search in another area or category.
        - If (False, None): No context available, treat as normal query.
    """
    resort = get_last_country_resort(user_id)
    if not resort:
        return False, user_message

    name = resort.get("name", "Загородный клуб")
    cat = resort.get("category", "")
    loc = resort.get("location", "")
    price = resort.get("price_range", "")
    features = resort.get("features", "")
    kid_friendly = resort.get("kid_friendly", "")
    why_best = resort.get("why_best", "")
    tip = resort.get("booking_tip", "")

    resort_context = (
        f"БАЗА ОТДЫХА: {name} ({cat})\n"
        f"Локация и дорога: {loc}\n"
        f"Стоимость: {price}\n"
        f"Инфраструктура и спа: {features}\n"
        f"Для детей и семьи: {kid_friendly}\n"
        f"Особенности: {why_best}\n"
        f"Лайфхак бронирования: {tip}\n"
    )

    history = get_country_chat_history(user_id)
    history_lines = []
    for h in history[-4:]:
        role_label = "Пользователь" if h.get("role") == "user" else "Консьерж"
        history_lines.append(f"{role_label}: {h.get('text', '')}")
    history_context = "\n".join(history_lines) if history_lines else "Диалог только начат."

    prompt = f"""Ты — персональный эксперт-консьерж по загородному премиальному и семейному отдыху в СПб, Ленинградской области и Карелии.
Пользователь сейчас просматривает конкретную загородную базу отдыха / отель и ведет с тобой живой диалог.

ТЕКУЩАЯ БАЗА ОТДЫХА:
{resort_context}

ПРЕДЫДУЩИЙ ДИАЛОГ:
{history_context}

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ:
«{user_message}»

ИНСТРУКЦИЯ:
Определи намерение пользователя:

ВАРИАНТ А: Пользователь задает ВОПРОС или ОБЩАЕТСЯ о текущей базе отдыха (о детях, бассейне, бане, рыбалке, собаках/pet-friendly, питании, номерах, ценах, бронировании, дороге, парковке, впечатлениях или просит совет).
Примеры: «А можно с собакой?», «Сколько стоит баня на 4 человека?», «Есть ли подогрев в открытом бассейне?», «Что есть для ребенка 4 года?», «Как лучше доехать без машины?», «А ресторан на территории дорогой?», «Входит ли завтрак?».
-> Ответь развернуто, доброжелательно, экспертно и по существу!
-> Используй форматирование Telegram HTML: <b>жирный</b>, <i>курсив</i>, списки, эмодзи.
-> Если точная информация не указана в карточке, ответь на основе реальных знаний об этом загородном клубе ({name}) и дай практический совет консьержа.

ВАРИАНТ Б: Пользователь просит СОВЕРШЕННО НОВЫЙ ПОИСК другой локации или другой категории (например: «найди теперь глэмпинг в Карелии», «хочу спа-отель в Зеленогорске», «покажи коттедж в Выборге»).
-> Верни СТРОГО JSON: {{"is_new_search": true, "query": "очищенный поисковый запрос пользователя"}}

Если это ответ по Варианту А — верни ТОЛЬКО текст твоего ответа на русском языке (без JSON).
Если это Вариант Б — верни СТРОГО JSON без лишних слов.
"""

    client = get_genai_client()
    for model_name in CANDIDATE_MODELS:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if resp and resp.text:
                raw_answer = resp.text.strip()
                if "is_new_search" in raw_answer:
                    m = re.search(r"\{.*\}", raw_answer, re.DOTALL)
                    if m:
                        try:
                            data = json.loads(m.group(0))
                            if data.get("is_new_search"):
                                new_q = data.get("query", user_message).strip()
                                return False, new_q
                        except Exception:
                            pass

                add_country_chat_turn(user_id, "user", user_message)
                add_country_chat_turn(user_id, "model", raw_answer)
                return True, raw_answer
        except Exception as e:
            logger.warning(f"Country relax advisor model {model_name} failed: {e}")

    return False, user_message
