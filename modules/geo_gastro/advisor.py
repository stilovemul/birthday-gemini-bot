import json
import logging
import re
from typing import Optional, Dict, Any, Tuple
from core.gemini import get_genai_client, CANDIDATE_MODELS
from modules.geo_gastro.storage import (
    get_last_gastro_recommendations,
    add_gastro_chat_turn
)

logger = logging.getLogger("GeoGastroAdvisor")


async def process_gastro_conversation(user_id: int, user_message: str) -> Tuple[bool, Optional[str]]:
    """
    Analyzes user message in the context of currently recommended restaurants.
    Returns:
        (is_followup: bool, response_or_new_query: Optional[str])
        - If (True, answer_text): This was a question/discussion about the restaurants, answer_text is the formatted reply.
        - If (False, new_search_query): This was a request for a brand new search in another area or cuisine.
        - If (False, None): No context available, treat as new search.
    """
    rec = get_last_gastro_recommendations(user_id)
    places = rec.get("places", [])
    if not places:
        return False, user_message

    # Build restaurant overview
    places_lines = []
    for i, p in enumerate(places, 1):
        name = p.get("name", f"Заведение #{i}")
        p_type = p.get("type", "")
        rating = p.get("rating", "")
        avg_bill = p.get("avg_bill", "")
        dishes = p.get("signature_dishes", "")
        vibe = p.get("vibe_description", "")
        addr = p.get("address", "")
        places_lines.append(
            f"Заведение #{i}: {name} ({p_type})\n"
            f"- Рейтинг: {rating} | Средний чек: {avg_bill}\n"
            f"- Адрес: {addr}\n"
            f"- Коронные блюда: {dishes}\n"
            f"- Вайб и особенности: {vibe}\n"
        )
    places_context = "\n".join(places_lines)

    chat_history = rec.get("chat_history", [])
    history_lines = []
    for h in chat_history[-4:]:
        role_label = "Пользователь" if h.get("role") == "user" else "Сомелье"
        history_lines.append(f"{role_label}: {h.get('text', '')}")
    history_context = "\n".join(history_lines) if history_lines else "Диалог только начат."

    prompt = f"""Ты — профессиональный ресторанный сомелье, гастрономический гид и ресторанный критик.
Пользователь только что получил подборку ресторанов и сейчас общается с тобой в чате.

ТЕКУЩАЯ ПОДБОРКА РЕСТОРАНОВ У ПОЛЬЗОВАТЕЛЯ:
{places_context}

ПРЕДЫДУЩИЙ ДИАЛОГ:
{history_context}

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ:
«{user_message}»

ИНСТРУКЦИЯ:
Определи намерение пользователя:

ВАРИАНТ А: Пользователь задает ВОПРОС или ОБЩАЕТСЯ о показанных заведениях (или о еде/вине/брони/парковке/детях/собаках/ценах/сравнении мест/дороге/совете что выбрать).
Примеры: «А в первом есть детская комната?», «Что лучше взять в Ferma?», «Какое вино подойдет к оленине?», «А парковка есть?», «В каком из них красивее вид?», «А бронь нужна?», «Сколько выйдет на двоих?», «А можно со своим алкоголем?», «Расскажи подробнее про шефа».
-> Ответь развернуто, живо, со вкусом и знанием ресторанной культуры Петербурга!
-> Используй форматирование Telegram HTML: <b>жирный</b>, <i>курсив</i>, списки, эмодзи.
-> В конце дай один меткий совет сомелье.

ВАРИАНТ Б: Пользователь просит СОВЕРШЕННО НОВЫЙ ПОИСК в другой локации, районе или кухне.
Примеры: «найди суши на Василеостровской», «где поесть пиццу у метро Пионерская», «хочу стейк в центре», «покажи кофейни в Петроградке».
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
                # Check for JSON new search
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

                # It's an insightful conversational reply
                add_gastro_chat_turn(user_id, "user", user_message)
                add_gastro_chat_turn(user_id, "model", raw_answer)
                return True, raw_answer
        except Exception as e:
            logger.warning(f"Gastro advisor model {model_name} failed: {e}")

    return False, user_message
