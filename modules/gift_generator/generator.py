import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini
from modules.birthdays.storage import get_sorted_birthdays

logger = logging.getLogger("GiftGenerator")

async def generate_gift_ideas(user_id: int, query_or_person: str, budget: str = "") -> Dict[str, Any]:
    birthdays = get_sorted_birthdays()
    b_summary = [f"{b['name']} ({b['day']}.{b['month']}, {b.get('turning_age', '')} лет) - {b.get('note', '')}" for b in birthdays[:10]]

    prompt = f"""Ты — премиальный сомелье подарков, впечатлений и сюрпризов.
База близких пользователя (для контекста): {'; '.join(b_summary)}

Запрос пользователя / Для кого подарок / Увлечения / Бюджет: '{query_or_person}' (Бюджет: {budget or 'не указан'})

Сгенерируй 4-5 ОРИГИНАЛЬНЫХ, небанальных и эмоциональных идей подарков (гаджеты, сертификаты на яркие впечатления, уютные вещи, персонализированные подарки).

СТРУКТУРА JSON:
1. "recipient_summary": Описание получателя и подход к выбору
2. "gifts": Список 4-5 подарков:
   - "title": Название подарка
   - "category": Категория (Впечатление, Гаджет, Стиль, Уют, Хобби)
   - "price_est": Примерная стоимость (в рублях)
   - "why_awesome": Почему вызовет вау-эффект и искреннюю радость
   - "where_to_buy": Где купить / заказать (маркетплейсы, сервисы впечатлений, магазины)
3. "presentation_idea": Как эффектно вручить подарок (креативная упаковка или момент).

Верни ответ СТРОГО в формате JSON:
{{
  "recipient_summary": "Подарок с душой и практической пользой",
  "gifts": [
    {{
      "title": "Полет в аэротрубе на двоих / Мастер-класс дрифта на автодроме Игора Драйв",
      "category": "Яркое впечатление",
      "price_est": "5 000 – 8 500 ₽",
      "why_awesome": "Адреналин, новые эмоции и памятные видео, которые запомнятся на всю жизнь.",
      "where_to_buy": "Сайт автодрома Игора Драйв / FlyStation СПб"
    }}
  ],
  "presentation_idea": "Вложите сертификат в коробку с миниатюрной машинкой или моделью самолета."
}}
"""
    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing gift json: {e}")

    return {
        "recipient_summary": "Отличные идеи подарков",
        "gifts": [
            {
                "title": "Умная колонка Яндекс Станция / Сертификат на спа",
                "category": "Универсальный",
                "price_est": "5 000 – 10 000 ₽",
                "why_awesome": "Полезно и приятно каждый день.",
                "where_to_buy": "Маркетплейсы / Яндекс Маркет"
            }
        ],
        "presentation_idea": "Красивая крафтовая упаковка с открыткой от руки."
    }
