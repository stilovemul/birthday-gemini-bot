import json
import os
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR, MSK_TZ

logger = logging.getLogger("SubscriptionStorage")
SUBS_FILE = DATA_DIR / "subscriptions.json"

DEFAULT_SUBSCRIPTIONS = [
    {
        "id": "sub_ya_plus",
        "user_id": 157236577,
        "name": "Яндекс Плюс",
        "amount": 299,
        "currency": "₽",
        "billing_cycle": "monthly",
        "payment_day": 15,
        "next_payment_date": "2026-09-15",
        "category": "Медиа & Музыка",
        "card_comment": "Основная карта",
        "auto_renew": True,
        "last_notified": ""
    },
    {
        "id": "sub_mobile_tel",
        "user_id": 157236577,
        "name": "Мобильная связь",
        "amount": 650,
        "currency": "₽",
        "billing_cycle": "monthly",
        "payment_day": 20,
        "next_payment_date": "2026-09-20",
        "category": "Связь & Интернет",
        "card_comment": "Автоплатеж",
        "auto_renew": True,
        "last_notified": ""
    },
    {
        "id": "sub_home_internet",
        "user_id": 157236577,
        "name": "Домашний интернет",
        "amount": 550,
        "currency": "₽",
        "billing_cycle": "monthly",
        "payment_day": 1,
        "next_payment_date": "2026-10-01",
        "category": "Дом & Интернет",
        "card_comment": "Сбер",
        "auto_renew": True,
        "last_notified": ""
    }
]


def _load_raw() -> List[Dict[str, Any]]:
    if not SUBS_FILE.exists():
        _save_raw(DEFAULT_SUBSCRIPTIONS)
        return list(DEFAULT_SUBSCRIPTIONS)
    try:
        with open(SUBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading subscriptions: {e}")
        return []


def _save_raw(data: List[Dict[str, Any]]) -> None:
    try:
        with open(SUBS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving subscriptions: {e}")


def get_user_subscriptions(user_id: int = 157236577) -> List[Dict[str, Any]]:
    subs = _load_raw()
    user_subs = [s for s in subs if s.get("user_id") == user_id]
    
    # Calculate days left for each subscription
    today = datetime.now(MSK_TZ).date()
    for s in user_subs:
        np_str = s.get("next_payment_date", "")
        if np_str:
            try:
                np_date = datetime.strptime(np_str, "%Y-%m-%d").date()
                # If date passed, advance to current/next cycle
                while np_date < today:
                    if s.get("billing_cycle") == "yearly":
                        np_date = date(np_date.year + 1, np_date.month, min(np_date.day, 28))
                    else:
                        month = np_date.month + 1
                        year = np_date.year
                        if month > 12:
                            month = 1
                            year += 1
                        np_date = date(year, month, min(s.get("payment_day", np_date.day), 28))
                    s["next_payment_date"] = np_date.strftime("%Y-%m-%d")
                
                days_left = (np_date - today).days
                s["days_left"] = days_left
            except Exception:
                s["days_left"] = 999
        else:
            s["days_left"] = 999

    user_subs.sort(key=lambda x: x.get("days_left", 999))
    _save_raw(subs)
    return user_subs


def add_subscription(
    user_id: int,
    name: str,
    amount: float,
    payment_day: int,
    category: str = "Сервисы",
    billing_cycle: str = "monthly",
    card_comment: str = "Карта"
) -> Dict[str, Any]:
    subs = _load_raw()
    today = datetime.now(MSK_TZ).date()
    
    # Compute next payment date
    day = max(1, min(payment_day, 28))
    if today.day <= day:
        next_dt = date(today.year, today.month, day)
    else:
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year += 1
        next_dt = date(year, month, day)

    sub_id = f"sub_{uuid.uuid4().hex[:8]}"
    item = {
        "id": sub_id,
        "user_id": user_id,
        "name": name.strip(),
        "amount": round(amount),
        "currency": "₽",
        "billing_cycle": billing_cycle,
        "payment_day": day,
        "next_payment_date": next_dt.strftime("%Y-%m-%d"),
        "category": category.strip(),
        "card_comment": card_comment.strip(),
        "auto_renew": True,
        "last_notified": ""
    }
    subs.append(item)
    _save_raw(subs)
    return item


def delete_subscription(user_id: int, sub_id: str) -> bool:
    subs = _load_raw()
    initial_len = len(subs)
    subs = [s for s in subs if not (s.get("id") == sub_id and s.get("user_id") == user_id)]
    if len(subs) < initial_len:
        _save_raw(subs)
        return True
    return False


def get_subscription_stats(user_id: int = 157236577) -> Dict[str, Any]:
    subs = get_user_subscriptions(user_id)
    monthly_total = 0
    yearly_total = 0
    categories: Dict[str, int] = {}

    for s in subs:
        amt = s.get("amount", 0)
        cycle = s.get("billing_cycle", "monthly")
        cat = s.get("category", "Другое")

        if cycle == "yearly":
            m_equiv = amt / 12.0
            y_equiv = amt
        else:
            m_equiv = amt
            y_equiv = amt * 12

        monthly_total += m_equiv
        yearly_total += y_equiv
        categories[cat] = categories.get(cat, 0) + int(m_equiv)

    return {
        "total_count": len(subs),
        "monthly_total": round(monthly_total),
        "yearly_total": round(yearly_total),
        "categories": categories,
        "items": subs
    }
