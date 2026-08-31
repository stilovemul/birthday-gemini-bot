import json
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR, MSK_TZ

logger = logging.getLogger("CustomRulesStorage")
RULES_FILE = DATA_DIR / "custom_rules.json"

DEFAULT_RULES = [
    {
        "id": "rule_counters_20th",
        "user_id": 157236577,
        "title": "💧 Передать показания счетчиков воды и света",
        "trigger_type": "monthly_day",
        "day_of_month": 20,
        "hour": 12,
        "minute": 0,
        "days_of_week": [],
        "action_text": "Пора передать показания счетчиков воды (ХВС/ГВС) и электричества в Петроэлектросбыт/УК!",
        "is_active": True,
        "last_triggered": ""
    },
    {
        "id": "rule_vitamins_morning",
        "user_id": 157236577,
        "title": "💊 Принять утренние витамины и Омега-3",
        "trigger_type": "daily_time",
        "day_of_month": 0,
        "hour": 9,
        "minute": 15,
        "days_of_week": [],
        "action_text": "Не забудьте выпить витамины и стакан воды для бодрого начала дня!",
        "is_active": True,
        "last_triggered": ""
    },
    {
        "id": "rule_friday_weekend_weather",
        "user_id": 157236577,
        "title": "🌤 Прогноз погоды на выходные",
        "trigger_type": "weekly_day",
        "day_of_month": 0,
        "hour": 18,
        "minute": 0,
        "days_of_week": [4],  # Friday (0=Monday, 4=Friday, 6=Sunday)
        "action_text": "Пятничный вечер! Завтра выходные — самое время проверить планы на загородную поездку или прогулку.",
        "is_active": True,
        "last_triggered": ""
    }
]


def _load_raw() -> List[Dict[str, Any]]:
    if not RULES_FILE.exists():
        _save_raw(DEFAULT_RULES)
        return list(DEFAULT_RULES)
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading custom rules: {e}")
        return []


def _save_raw(data: List[Dict[str, Any]]) -> None:
    try:
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving custom rules: {e}")


def get_user_rules(user_id: int = 157236577) -> List[Dict[str, Any]]:
    rules = _load_raw()
    return [r for r in rules if r.get("user_id") == user_id]


def add_custom_rule(
    user_id: int,
    title: str,
    trigger_type: str,
    action_text: str,
    hour: int = 12,
    minute: int = 0,
    day_of_month: int = 0,
    days_of_week: Optional[List[int]] = None
) -> Dict[str, Any]:
    rules = _load_raw()
    rule_id = f"rule_{uuid.uuid4().hex[:8]}"
    item = {
        "id": rule_id,
        "user_id": user_id,
        "title": title.strip(),
        "trigger_type": trigger_type,
        "day_of_month": day_of_month,
        "hour": hour,
        "minute": minute,
        "days_of_week": days_of_week or [],
        "action_text": action_text.strip(),
        "is_active": True,
        "last_triggered": ""
    }
    rules.append(item)
    _save_raw(rules)
    return item


def toggle_rule_state(user_id: int, rule_id: str) -> Optional[bool]:
    rules = _load_raw()
    for r in rules:
        if r.get("id") == rule_id and r.get("user_id") == user_id:
            r["is_active"] = not r.get("is_active", True)
            _save_raw(rules)
            return r["is_active"]
    return None


def delete_custom_rule(user_id: int, rule_id: str) -> bool:
    rules = _load_raw()
    initial_len = len(rules)
    rules = [r for r in rules if not (r.get("id") == rule_id and r.get("user_id") == user_id)]
    if len(rules) < initial_len:
        _save_raw(rules)
        return True
    return False
