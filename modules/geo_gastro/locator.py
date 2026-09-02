import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("GeoGastroLocator")

async def find_places(user_id: int, query_or_city: str, lat: float = None, lon: float = None, is_speakeasy: bool = False) -> Dict[str, Any]:
    geo_hint = f"Координаты GPS: широта {lat}, долгота {lon} (поиск в радиусе 1 км)" if lat and lon else ""
    cat_type = "Секретные Спикизи-Бары (Speakeasy, тайные входы, авторские коктейли)" if is_speakeasy else "Топовые рестораны, кафе и гастрономические споты"

    prompt = f"""Ты — профессиональный ресторанный критик и гастрономический сомелье.
Категория поиска: {cat_type}
Локация / Город / Запрос: '{query_or_city}' {geo_hint}

Подбери 3-4 РЕАЛЬНО выдающихся, проверенных заведения (где действительно потрясающе вкусно, самобытно и высокий сервис).

СТРУКТУРА JSON:
1. "search_summary": Краткое резюме гастрономической подборки.
2. "places": Список 3-4 заведений:
   - "name": Название заведения
   - "type": Тип (Мясной ресторан, Итальянская остерия, Спикизи-бар, Азиатское бистро, Спешелти-кофейня)
   - "rating": Честный рейтинг (например, «Яндекс: 4.9 | 2ГИС: 4.8»)
   - "avg_bill": Средний чек (например, «1 500 – 2 500 ₽»)
   - "signature_dishes": 2-3 коронных блюда/напитка, ради которых СТОИТ прийти
   - "vibe_description": Атмосфера, интерьер, сервис и фишка (для спикизи — секрет входа: через шкаф, телефонную будку, пароль)
   - "address": Точный адрес и ориентир
3. "sommelier_tip": Экспертный совет (нужна ли бронь стола, какой столик выбрать, время счастливых часов).

Верни ответ СТРОГО в формате JSON:
{{
  "search_summary": "Топ-3 проверенных гастрономических места рядом с вами",
  "places": [
    {{
      "name": "Smoke BBQ",
      "type": "Мясной ресторан и крафтовый бар",
      "rating": "⭐️ 4.9 (Яндекс Карты)",
      "avg_bill": "2 000 – 3 500 ₽",
      "signature_dishes": "Брискет из коптильни 18 часов, свиные ребра BBQ, копченый тартар",
      "vibe_description": "Брутальный лофт, техасский смокер на открытой кухне, эталонный выбор бурбона и пива.",
      "address": "ул. Рубинштейна, 11 (м. Достоевская)"
    }}
  ],
  "sommelier_tip": "💡 В пятницу и выходные обязательно бронируйте стол за 1-2 дня. Столики у открытой кухни самые атмосферные."
}}
"""
    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing gastro json: {e}")

    return {
        "search_summary": "Рекомендованные рестораны высокой кухни",
        "places": [
            {
                "name": "Duo Gastrobar",
                "type": "Авторская кухня",
                "rating": "⭐️ 4.9",
                "avg_bill": "1 800 – 2 800 ₽",
                "signature_dishes": "Тартар из говядины с пармезаном, гребешки с кремом из цветной капусты",
                "vibe_description": "Уютный гастробар с эталонной подачей и лаконичным меню.",
                "address": "ул. Кирочная, 8А"
            }
        ],
        "sommelier_tip": "Рекомендуем бронировать столик заранее."
    }
