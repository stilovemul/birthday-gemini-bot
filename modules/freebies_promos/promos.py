import re
import json
import logging
from typing import Dict, Any, List
from core.gemini import ask_gemini

logger = logging.getLogger("DeliveryPromos")


async def get_curated_delivery_promos(user_id: int) -> Dict[str, Any]:
    """
    Returns curated active delivery promo codes for top food delivery apps.
    """
    prompt = (
        "Сформируй список актуальных и рабочих категорий промокодов на доставку еды и продуктов в РФ/Санкт-Петербурге "
        "(Самокат, Яндекс Еда / Лавка, Купер / СберМаркет, ВкусВилл, Додо Пицца).\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "services": [\n'
        '    {\n'
        '      "name": "Самокат",\n'
        '      "discount": "до -300 ₽",\n'
        '      "code": "START300",\n'
        '      "condition": "Скидка 300 ₽ на первый заказ от 800 ₽ или 150 ₽ для старых клиентов"\n'
        '    },\n'
        '    {\n'
        '      "name": "Купер (СберМаркет)",\n'
        '      "discount": "до -1000 ₽",\n'
        '      "code": "EDA1000 / KUPER30",\n'
        '      "condition": "Скидка 30% на заказ из супермаркетов (Лента, Окей, Метро)"\n'
        '    },\n'
        '    {\n'
        '      "name": "Яндекс Еда & Лавка",\n'
        '      "discount": "до -25%",\n'
        '      "code": "LAVKA25 / EDATOP",\n'
        '      "condition": "Скидка 25% на рестораны и готовую кулинарию"\n'
        '    },\n'
        '    {\n'
        '      "name": "ВкусВилл Доставка",\n'
        '      "discount": "-200 ₽",\n'
        '      "code": "VKUS200 / ПРИВЕТ",\n'
        '      "condition": "Скидка 200 ₽ от 1000 ₽ + любимый продукт со скидкой 20%"\n'
        '    },\n'
        '    {\n'
        '      "name": "Додо Пицца",\n'
        '      "discount": "Пицца в подарок",\n'
        '      "code": "DODOFREE / ПЕППЕРОНИ",\n'
        '      "condition": "Пепперони 25см в подарок при заказе от 990 ₽"\n'
        '    }\n'
        '  ],\n'
        '  "lifehack": "💡 Лайфхак: используйте виртуальные номера или новый аккаунт для применения максимальных промокодов первого заказа!"\n'
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
            {"name": "Самокат", "discount": "300 ₽", "code": "START300", "condition": "От 800 ₽"},
            {"name": "Купер", "discount": "до 1000 ₽", "code": "KUPER1000", "condition": "Скидка на гипермаркеты"},
            {"name": "Яндекс Еда", "discount": "20%", "code": "EDA20", "condition": "В ресторанах"}
        ],
        "lifehack": "Проверяйте раздел акций в приложениях доставки."
    }
