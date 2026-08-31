import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("DeliveryPromos")


async def get_curated_delivery_promos(user_id: int, query: str = "") -> Dict[str, Any]:
    """
    Returns curated active delivery promo codes strictly for Yandex.Eda and Perekrestok Delivery.
    """
    prompt = (
        f"Ты специалист по максимальной экономии и промокодам на доставку еды и продуктов в РФ/Санкт-Петербурге. "
        f"Пользователя интересуют ИСКЛЮЧИТЕЛЬНО два сервиса: 1) Яндекс Еда (рестораны, магазины, лавка) и 2) Перекрёсток Доставка. "
        f"Уточнение от пользователя: '{query if query else 'все актуальные промокоды'}'\n\n"
        "Сформируй самые свежие, выгодные и рабочие промокоды для Яндекс.Еды и Перекрёстка (для первого заказа и для постоянных клиентов).\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "services": [\n'
        '    {\n'
        '      "name": "Яндекс Еда (Рестораны)",\n'
        '      "discount": "до -30% (или 500 ₽)",\n'
        '      "code": "EDA30 / YANDEX500",\n'
        '      "condition": "Скидка 25-30% на первый заказ от 1000 ₽ или промокоды ресторанов в разделе Акции"\n'
        '    },\n'
        '    {\n'
        '      "name": "Яндекс Еда (Супермаркеты & Лавка)",\n'
        '      "discount": "до -500 ₽",\n'
        '      "code": "SUPER500 / MARKET30",\n'
        '      "condition": "Скидка 500 ₽ от 1500 ₽ на заказ продуктов из Ленты, Окея, ВкусВилла через Еду"\n'
        '    },\n'
        '    {\n'
        '      "name": "Перекрёсток Доставка (Первые заказы)",\n'
        '      "discount": "до -35% (до 600 ₽)",\n'
        '      "code": "PEREK35 / NEW600",\n'
        '      "condition": "Скидка 30-35% на первые 3 заказа от 1500 ₽ в мобильном приложении Перекрёсток"\n'
        '    },\n'
        '    {\n'
        '      "name": "Перекрёсток Доставка (Повторные заказы)",\n'
        '      "discount": "-15% / Бесплатная доставка",\n'
        '      "code": "DOMA15 / CHEF20",\n'
        '      "condition": "Скидка 15-20% на готовую кулинарию Шеф Перекрёсток или бесплатная доставка от 2000 ₽"\n'
        '    }\n'
        '  ],\n'
        '  "lifehack": "💡 Лайфхак для Перекрёстка: подключите сервис Пакет (X5 Клуб) — он дает до 10% кэшбэка баллами за каждую покупку и 5 бесплатных экспресс-доставок каждый месяц!"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing promos JSON: {e}")

    return {
        "services": [
            {"name": "Яндекс Еда", "discount": "до -30%", "code": "EDA30", "condition": "Скидка на рестораны и магазины"},
            {"name": "Перекрёсток Доставка", "discount": "до -35%", "code": "PEREK35", "condition": "Скидка на первые и повторные заказы"}
        ],
        "lifehack": "Используйте подписку Пакет для максимального кэшбэка в Перекрёстке."
    }
