import json
import logging
import re
from typing import Tuple, Dict, Any, Optional
from google.genai import types
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("FoodAnalyzer")

NUTRITIONIST_SYSTEM_PROMPT = """Ты — профессиональный ИИ-нутрициолог и эксперт по подсчету калорий и КБЖУ.
Твоя задача — внимательно изучить фотографию блюда/продуктов и выдать структурированный JSON-анализ.

ФОРМАТ ОТВЕТА СТРОГО JSON:
{
  "is_food": true,
  "dish_name": "Название блюда на русском языке",
  "estimated_weight_g": 350,
  "calories": 450,
  "protein": 32.0,
  "fat": 14.5,
  "carbs": 48.0,
  "ingredients": [
    {"name": "Куриное филе", "weight": "150г", "kcal": 240, "p": 38.0, "f": 3.5, "c": 0.0},
    {"name": "Рис басмати", "weight": "150г", "kcal": 180, "p": 4.0, "f": 0.5, "c": 39.0},
    {"name": "Оливковое масло / заправка", "weight": "10г", "kcal": 90, "p": 0.0, "f": 10.0, "c": 0.0}
  ],
  "healthy_verdict": "Краткая экспертная оценка полезности и совет по приёму пищи на русском (1-2 предложения)."
}

Если на фото НЕТ еды или напитков, верни:
{
  "is_food": false,
  "reason": "На фото не обнаружены продукты питания или напитки."
}

Оценивай порции реалистично. Будь точен с белками, жирами и углеводами.
Верни ТОЛЬКО чистый валидный JSON без лишнего текста вокруг."""


async def analyze_food_photo(image_bytes: bytes, user_comment: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Analyzes a photo of food using Gemini Vision and returns parsed nutritional data.
    Returns (is_food, food_data_dict, raw_or_error_message).
    """
    c = get_genai_client()
    prompt_text = "Проанализируй блюдо на этом фото, определи ингредиенты, примерный вес порции и рассчитай калории (КБЖУ)."
    if user_comment:
        prompt_text += f"\nКомментарий пользователя к фото: «{user_comment}»"

    contents = [
        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        prompt_text
    ]

    for model_name in CANDIDATE_MODELS:
        try:
            resp = await c.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=NUTRITIONIST_SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            if resp and resp.text:
                raw_text = resp.text.strip()
                # Clean markdown blocks if any
                clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE).strip()
                
                data = json.loads(clean_json)
                if not data.get("is_food"):
                    return False, None, data.get("reason", "На фото не обнаружена еда.")
                
                logger.info(f"Successfully analyzed food via {model_name}: {data.get('dish_name')} ({data.get('calories')} kcal)")
                return True, data, ""
        except Exception as e:
            logger.warning(f"Model {model_name} failed food analysis: {e}. Trying fallback...")

    return False, None, "Не удалось распознать блюдо на фото. Попробуйте сфотографировать ближе и при хорошем освещении."
