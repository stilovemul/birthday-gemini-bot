import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("PhotoSpotsHunter")

async def find_cinematic_photo_spots(user_id: int, city_or_vibe: str) -> Dict[str, Any]:
    prompt = f"""Ты — профессиональный кинематографист, фотограф и скаут локаций для кино и сочных рилс/фото.
Город / Локация / Стилистика: '{city_or_vibe}'

Подбери 3-4 САМЫХ атмосферных, визуально сильных и кинематографичных фотолокаций (СПб, Ленобласть или любой запрошенный город мира).

СТРУКТУРА JSON:
1. "collection_title": Название подборки локаций
2. "spots": Список 3-4 локаций:
   - "name": Название места
   - "address_or_coords": Адрес или координаты
   - "cinematic_style": Стиль (Киберпанк/Неон, Брутальный урбан, Дворянский шик, Нордическая природа, Песчаные дюны)
   - "best_time": Идеальное время суток (Золотой час на закате, Синий час, Ночь)
   - "camera_angles": 2 конкретных совета по ракурсу и кадрированию
   - "access_notes": Как пройти / платный ли вход / дресс-код
3. "editing_preset_tip": Совет по цветокоррекции фото (какие тона подкрутить).

Верни ответ СТРОГО в формате JSON:
{{
  "collection_title": "Топ кинематографичных фотолокаций Санкт-Петербурга",
  "spots": [
    {{
      "name": "Песчаные дюны и коряги на мысе Комарово / Сестрорецк",
      "address_or_coords": "пос. Комарово, Приморское шоссе, эко-тропа",
      "cinematic_style": "Нордическая меланхолия и простор Финского залива (в духе скандинавского кино)",
      "best_time": "За 40 минут до заката (мягкий золотой свет над водой)",
      "camera_angles": "Снимайте на уровне песка с отражением в мелкой кромке воды, либо силуэт на фоне заходящего солнца.",
      "access_notes": "Свободный вход, удобная парковка вдоль шоссе."
    }}
  ],
  "editing_preset_tip": "🎨 Приглушите зелень, добавьте тепла в света и легкий сине-бирюзовый оттенок в тени для киношного контраста."
}}
"""
    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing photo spots json: {e}")

    return {
        "collection_title": "Атмосферные фотолокации",
        "spots": [
            {
                "name": "Севкабель Порт и набережная залива",
                "address_or_coords": "Кожевенная линия, 40",
                "cinematic_style": "Индустриальный лофт и морской вид",
                "best_time": "Закат",
                "camera_angles": "Широкий угол с видом на вантовый мост ЗСД.",
                "access_notes": "Свободный вход."
            }
        ],
        "editing_preset_tip": "Контрастный кино-стиль с теплыми закатными лучами."
    }
