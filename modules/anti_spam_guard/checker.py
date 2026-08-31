import re
import json
import logging
from typing import Dict, Any
from core.gemini import ask_gemini

logger = logging.getLogger("AntiSpamChecker")


async def check_phone_number_reputation(user_id: int, raw_phone: str) -> Dict[str, Any]:
    """
    Analyzes phone number for spam category, telecom operator, and scam threat score.
    """
    clean_digits = re.sub(r"\D", "", raw_phone)
    prompt = (
        f"Ты аналитик телефонного спама и кибербезопасности. Проанализируй номер телефона: '{raw_phone}' (цифры: {clean_digits}).\n\n"
        "Определи:\n"
        "1. formatted_phone: Красивый формат (+7 (XXX) XXX-XX-XX).\n"
        "2. operator_region: Вероятный оператор и регион (например: 'МТС, г. Санкт-Петербург' или 'Мегафон, Москва' или 'Виртуальный номер Телфин/Zadarma').\n"
        "3. reputation: Статус ('🚨 Высокая угроза: Мошенники / Fake-Сбер', '⚠️ Навязчивая реклама / Опросы', '🏢 Официальная организация / Служба доставки', '✅ Безопасный / Обычный абонент').\n"
        "4. spam_score: Оценка спама от 0 до 100 (где 0 = кристально чистый, 100 = 100% мошенники).\n"
        "5. category: Категория ('Банки & Кредиты', 'Инвестиции / Биржи', 'Стоматология & Медцентры', 'Коллекторы', 'Фальшивая полиция/ФСБ', 'Доставка / Курьеры', 'Физическое лицо').\n"
        "6. recommendation: Четкая рекомендация ('Сбросить и заблокировать', 'Не называть SMS-коды', 'Можно брать трубку').\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "phone": "+7 (812) 456-78-90",\n'
        '  "operator": "Ростелеком / Санкт-Петербург",\n'
        '  "reputation": "⚠️ Навязчивая реклама / Опросы",\n'
        '  "spam_score": 75,\n'
        '  "category": "Телемаркетинг & Услуги",\n'
        '  "recommendation": "Не берите трубку или добавьте в черный список."\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing spam checker JSON: {e}")

    return {
        "phone": raw_phone,
        "operator": "РФ / Мобильный",
        "reputation": "⚠️ Требует внимания",
        "spam_score": 50,
        "category": "Неизвестный номер",
        "recommendation": "Не сообщайте персональные данные и коды из СМС."
    }
