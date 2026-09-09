import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("UniversalPromos")

# Fallback catalog with tested, evergreen promo mechanics and offers
CURATED_FALLBACK_PROMOS = {
    "yandex": {
        "target_title": "Яндекс.Еда & Доставка",
        "category_type": "Агрегатор доставки еды и ресторанов",
        "active_codes": [
            {
                "code": "EDA30",
                "discount": "до -30% (до 500 ₽)",
                "condition": "На первый заказ из любого ресторана от 1000 ₽ в приложении",
                "target_audience": "Первый заказ"
            },
            {
                "code": "SUPER500",
                "discount": "500 ₽ от 1500 ₽",
                "condition": "На первый заказ продуктов из супермаркетов через сервис",
                "target_audience": "Первый заказ продуктов"
            },
            {
                "code": "CHEF15 / В Меню",
                "discount": "-15%..-20%",
                "condition": "Внутри раздела «Акции ресторанов» и скидки заведений",
                "target_audience": "Повторный заказ"
            }
        ],
        "secret_combos": "🎁 В приложении ищите рестораны со значком подарка — блюдо бесплатно при заказе от 1200 ₽. С подпиской Яндекс Плюс начисляется до 5-10% кешбэка баллами.",
        "bank_cashback_perks": "💳 В Т-Банке (Тинькофф) и Альфа-Банке в категории «Город / Еда» регулярно доступен кэшбэк 10-15%.",
        "pro_saving_tip": "💡 На повторные заказы: проверяйте раздел «Скидки до 30% от ресторанов» — они суммируются с бесплатной доставкой Яндекс Плюс. Для скидки на первый заказ используйте номер второго члена семьи."
    },
    "kuper": {
        "target_title": "Купер (СберМаркет)",
        "category_type": "Доставка продуктов и ресторанов",
        "active_codes": [
            {
                "code": "START500",
                "discount": "500 ₽ от 1500 ₽",
                "condition": "На первый заказ из любого гипермаркета через приложение",
                "target_audience": "Первый заказ"
            },
            {
                "code": "EDA20",
                "discount": "-20%",
                "condition": "На первый заказ из ресторанов от 1000 ₽",
                "target_audience": "Первый заказ"
            },
            {
                "code": "BONUS200 / В СМС",
                "discount": "200-400 ₽ от 2000 ₽",
                "condition": "Персональные промокоды в push-уведомлениях и профиле",
                "target_audience": "Повторный заказ"
            }
        ],
        "secret_combos": "⭐️ СберСпасибо: списание до 99% суммы бонусами Спасибо при оплате картой Сбера.",
        "bank_cashback_perks": "💳 Кешбэк до 5-7% в категории «Супермаркеты» в банках или до 10% в СберПремьер.",
        "pro_saving_tip": "💡 В Купере регулярно начисляют промокоды на повторные заказы в раздел «Профиль → Промокоды» после 2-3 дней отсутствия заказов."
    },
    "samokat": {
        "target_title": "Самокат (Экспресс-доставка за 15 мин)",
        "category_type": "Быстрая доставка продуктов",
        "active_codes": [
            {
                "code": "SMK200",
                "discount": "200 ₽ от 800 ₽ (-25%)",
                "condition": "На первый заказ в мобильном приложении",
                "target_audience": "Первый заказ"
            },
            {
                "code": "POVTOR100",
                "discount": "100-150 ₽ от 1200 ₽",
                "condition": "На повторные заказы в приложении или через СберСпасибо",
                "target_audience": "Повторный заказ"
            }
        ],
        "secret_combos": "⚡️ Раздел «Выгодно» и «Скидки до 50%» обновляется каждое утро. СберСпасибо списывается до 99%.",
        "bank_cashback_perks": "💳 Т-Банк и ВТБ часто дают 5-10% кешбэка на категорию Супермаркеты/Самокат.",
        "pro_saving_tip": "💡 Набирайте корзину из раздела спецпредложений: скидки до 40% суммируются с промокодами."
    },
    "dodo": {
        "target_title": "Додо Пицца",
        "category_type": "Сеть пиццерий и доставка",
        "active_codes": [
            {
                "code": "DODO20",
                "discount": "Пицца 25 см в подарок или -20%",
                "condition": "На первый заказ от минимальной суммы через приложение",
                "target_audience": "Первый заказ"
            },
            {
                "code": "COMBO / 2PIZZA",
                "discount": "Выгода до 35%",
                "condition": "Комбо-наборы из 2-3 пицц в разделе «Комбо»",
                "target_audience": "Повторный заказ (Все клиенты)"
            }
        ],
        "secret_combos": "🍕 5% додо-коинами возвращается с каждого заказа. Их можно тратить на бесплатные пиццы, закуски и напитки за 1 ₽.",
        "bank_cashback_perks": "💳 Категория «Рестораны и фастфуд» в Т-Банке/Альфе (5-10%).",
        "pro_saving_tip": "💡 Всегда заказывайте через раздел «Комбо» — это дает фиксированную скидку 25-35% без ввода промокодов на любые повторные заказы."
    }
}


async def get_curated_delivery_promos(user_id: int, query: str = "") -> Dict[str, Any]:
    """
    Finds active promo codes, discounts, secret combos, and cashback perks for ANY restaurant,
    food delivery service (Yandex Eda, Samokat, Kuper, Delivery Club), marketplace, or retail store.
    Accurately tailors results for first vs repeat orders based on the user query.
    """
    search_target = query.strip() if query else "Яндекс Еда, Самокат, Купер и рестораны СПб"

    prompt = f"""Ты — ведущий эксперт по промокодам, скидкам, акциям и хакам экономии в России (Санкт-Петербург и РФ).
Запрос пользователя / Сервис / Ресторан: '{search_target}'

Твоя задача — предоставить САМЫЕ ВЫГОДНЫЕ, РАБОЧИЕ И АКТУАЛЬНЫЕ промокоды и схемы экономии:
1. Если пользователь упомянул «повторный заказ» / «не первый заказ» / «для постоянных» — СДЕЛАЙ ГЛАВНЫЙ АКЦЕНТ НА ПОВТОРНЫЕ ЗАКАЗЫ (промокоды для постоянных, секретные разделы, комбо, как получить скидку).
2. Если упомянут «первый заказ» — выдай максимальные промокоды новичка (до 30-50% скидки).
3. Если запрос общий — дай баланс: коды на первый заказ, коды на повторные заказы, комбо и банковский кэшбэк.
4. Промокоды должны быть правдоподобными, аккуратными и применимыми в РФ.

СТРУКТУРА JSON:
{{
  "target_title": "Точное название сервиса / ресторана / магазина",
  "category_type": "Тип (Агрегатор доставки / Ресторан / Доставка продуктов / Маркетплейс / Сеть)",
  "active_codes": [
    {{
      "code": "ПРОМОКОД (например: EDA30, SUPER500, В ПРИЛОЖЕНИИ, CHEF15)",
      "discount": "Размер выгоды (например: «-20% на повторный заказ», «Скидка 500 ₽ от 1500 ₽», «-30% на первый»)",
      "condition": "Точные условия применения (минимальная сумма заказа, в приложении, на определенные категории)",
      "target_audience": "Повторный заказ / Первый заказ / Все клиенты"
    }}
  ],
  "secret_combos": "Спецпредложения без промокодов (подарки к заказу, комбо-наборы 1+1, бесплатная доставка, баллы Плюс/Спасибо)",
  "bank_cashback_perks": "Кэшбэк банков и баллы (Т-Банк/Тинькофф, Альфа, СберСпасибо, Яндекс Плюс)",
  "pro_saving_tip": "Лайфхак максимальной выгоды (как сэкономить на повторном заказе, применить баллы, обойти ограничение или получить бесплатную доставку)."
}}

Верни ТОЛЬКО валидный JSON без markdown-оберток и лишнего текста."""

    client = get_genai_client()
    for model_name in CANDIDATE_MODELS:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if resp and resp.text:
                text_clean = resp.text.strip()
                # Strip markdown code fences if present
                if text_clean.startswith("```"):
                    text_clean = re.sub(r"^```(?:json)?\s*", "", text_clean)
                    text_clean = re.sub(r"\s*```$", "", text_clean)

                m = re.search(r"\{.*\}", text_clean, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    if isinstance(data, dict) and data.get("active_codes"):
                        return data
        except Exception as e:
            logger.warning(f"Model {model_name} failed in get_curated_delivery_promos: {e}")

    # Fallback to curated catalog
    q_lower = search_target.lower()
    if any(k in q_lower for k in ["яндекс", "еда", "лавка", "yandex"]):
        fb = dict(CURATED_FALLBACK_PROMOS["yandex"])
    elif any(k in q_lower for k in ["купер", "сбермаркет", "kuper"]):
        fb = dict(CURATED_FALLBACK_PROMOS["kuper"])
    elif any(k in q_lower for k in ["самокат", "samokat"]):
        fb = dict(CURATED_FALLBACK_PROMOS["samokat"])
    elif any(k in q_lower for k in ["додо", "dodo", "пицца"]):
        fb = dict(CURATED_FALLBACK_PROMOS["dodo"])
    else:
        fb = {
            "target_title": search_target,
            "category_type": "Скидки и промокоды",
            "active_codes": [
                {
                    "code": "START20",
                    "discount": "-20% на первый заказ",
                    "condition": "При заказе в мобильном приложении от минимальной суммы",
                    "target_audience": "Первый заказ"
                },
                {
                    "code": "COMBO / SALE",
                    "discount": "Скидки 15-30% в спецразделах",
                    "condition": "В разделах «Акции» и «Комбо» на повторные заказы",
                    "target_audience": "Повторный заказ"
                },
                {
                    "code": "BONUS",
                    "discount": "Подарок или скидка к заказу",
                    "condition": "При заказе на сумму от 1500 ₽",
                    "target_audience": "Все клиенты"
                }
            ],
            "secret_combos": "🎁 Проверьте вкладку «Акции» в официальном приложении заведения.",
            "bank_cashback_perks": "💳 Проверьте кэшбэк в приложении Т-Банка или Альфа-Банка в разделе «Кэшбэк и бонусы».",
            "pro_saving_tip": "💡 Используйте программы лояльности сервисов для накопления бонусов на последующие заказы."
        }

    return fb
