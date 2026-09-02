import re
import json
import random
import logging
from typing import Dict, Any, List
from core.gemini import get_genai_client, CANDIDATE_MODELS
from modules.country_relax.curated_catalog import CURATED_COUNTRY_RESORTS
from modules.country_relax.storage import (
    get_seen_resorts,
    add_seen_resort,
    clear_seen_resorts,
    set_user_last_country
)

logger = logging.getLogger("CountryRelaxFinder")

CATEGORY_TAG_MAP = {
    "pool": "pool",
    "banya": "banya",
    "glamp": "glamping",
    "family": "family",
    "kids": "kids",
    "lake": "lake",
    "romantic": "romantic",
    "random": "general",
    "general": "general"
}


def pick_curated_resort(user_id: int, category: str = "general") -> Dict[str, Any]:
    """
    Выбирает проверенную загородную базу/отель из каталога,
    исключая ранее показанные пользователю варианты.
    """
    seen = get_seen_resorts(user_id)
    tag = CATEGORY_TAG_MAP.get(category, "general")

    # Фильтруем те, которые пользователь еще не видел
    unseen = [r for r in CURATED_COUNTRY_RESORTS if r["name"] not in seen]

    # Если просмотрел все 22, сбрасываем историю
    if not unseen:
        clear_seen_resorts(user_id)
        unseen = list(CURATED_COUNTRY_RESORTS)

    # Ищем совпадения по категории/тегу
    matching = [r for r in unseen if tag in r.get("tags", [])]
    pool = matching if matching else unseen

    chosen = random.choice(pool)
    add_seen_resort(user_id, chosen["name"])
    return chosen


async def find_country_resorts(
    user_id: int,
    query: str,
    category: str = "general",
    is_another: bool = False
) -> Dict[str, Any]:
    """
    Интеллектуальный подбор загородного отдыха:
    - При запросе пресетов или свободном запросе подбирает лучший вариант.
    - Исключает уже показанные базы (гарантия разнообразия и кнопки «Ещё»).
    - Использует Gemini Flash с ротацией моделей и fallback на экспертный каталог.
    """
    set_user_last_country(user_id, query, category)
    seen = get_seen_resorts(user_id)
    seen_text = "\n".join([f"- {s}" for s in seen[-6:]]) if seen else "Ранее базы не предлагались."

    variation_instruction = ""
    if is_another or seen:
        variation_instruction = (
            f"\n\nКАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО предлагать или повторять следующие уже просмотренные базы:\n"
            f"{seen_text}\n"
            f"ОБЯЗАТЕЛЬНО предложи совершенно ДРУГУЮ загородную базу/отель/глэмпинг/баню!"
        )

    prompt = f"""Ты — персональный консьерж по загородному премиальному и семейному отдыху в Санкт-Петербурге, Ленобласти и Карелии.
Категория: {category}
Запрос пользователя / Пожелания / Бюджет: '{query}'
{variation_instruction}

Подбери ОДНУ конкретную идеальную загородную базу отдыха, спа-отель, глэмпинг или банный комплекс под этот запрос.
Укажи честные актуальные данные: реальное расстояние от СПб, трассу, цены, особенности инфраструктуры и лайфхак бронирования.

СТРУКТУРА JSON:
{{
  "name": "Название базы / отеля / глэмпинга",
  "category": "Короткий атмосферный статус / категория (например: 🏊‍♂️ Спа & Теплый открытый бассейн)",
  "location": "Район, ориентир, расстояние в км от СПб и время в пути (например: Курортный р-н, Зеленогорск, 50 км от СПб, ~45 мин по ЗСД)",
  "price_range": "Ориентировочная стоимость за сутки (будни / выходные)",
  "features": "Бассейн с подогревом, русская баня, спа, купель, ресторан, мангалы",
  "kid_friendly": "Что есть для детей и семьи (площадки, анимация, детские комнаты, pet-friendly)",
  "why_best": "Почему это место идеально попадает в запрос (1-2 предложения)",
  "booking_tip": "Полезный совет по бронированию (какой домик/корпус лучше брать, когда бронировать, акции)",
  "geo_query": "Точное название для поиска на Яндекс.Картах"
}}

Верни ответ СТРОГО в формате JSON без разметки markdown:
"""

    try:
        client = get_genai_client()
        for model_name in CANDIDATE_MODELS:
            try:
                resp = await client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if resp and resp.text:
                    m = re.search(r"\{.*\}", resp.text, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        name = data.get("name", "").strip()
                        if name:
                            # Проверяем на дубликат
                            is_dup = any(prev.lower() in name.lower() for prev in seen[-5:])
                            if not is_dup:
                                add_seen_resort(user_id, name)
                                return data
            except Exception as ex:
                logger.warning(f"Country Relax Gemini model {model_name} error: {ex}")
    except Exception as e:
        logger.error(f"Error calling Gemini in Country Relax finder: {e}")

    # Надежный fallback из каталога 22 эталонных локаций без повторов
    return pick_curated_resort(user_id, category)
