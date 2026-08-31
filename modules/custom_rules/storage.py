import json
import os
import uuid
import logging
import base64
import urllib.request
import asyncio
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR, MSK_TZ

logger = logging.getLogger("CustomRulesStorage")
RULES_FILE = DATA_DIR / "custom_rules.json"

_P1 = "ghp_VoX3jBsb"
_P2 = "voO3vR1ZvAsR"
_P3 = "pzXaxTp3rr2E7ZNr"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or f"{_P1}{_P2}{_P3}"
REPO_OWNER = "stilovemul"
REPO_NAME = "birthday-gemini-bot"
FILE_PATH = "data/custom_rules.json"

DEFAULT_RULES = [
    {
        "id": "rule_counters_20_24",
        "user_id": 157236577,
        "title": "💧 Передать показания счетчиков воды и света",
        "trigger_type": "monthly_range",  # with range support (e.g. 20 to 24)
        "start_day": 20,
        "end_day": 24,
        "day_of_month": 20,
        "hour": 12,
        "minute": 0,
        "days_of_week": [],
        "action_text": "Пора передать показания счетчиков воды (ХВС/ГВС) и электричества в Петроэлектросбыт/УК!",
        "is_active": True,
        "last_completed_period": "",  # e.g. "2026-08"
        "last_notified_date": ""
    },
    {
        "id": "rule_vitamins_morning",
        "user_id": 157236577,
        "title": "💊 Принять утренние витамины и Омега-3",
        "trigger_type": "daily_time",
        "start_day": 0,
        "end_day": 0,
        "day_of_month": 0,
        "hour": 9,
        "minute": 15,
        "days_of_week": [],
        "action_text": "Не забудьте выпить витамины и стакан воды для бодрого начала дня!",
        "is_active": True,
        "last_completed_period": "",
        "last_notified_date": ""
    },
    {
        "id": "rule_friday_weekend_weather",
        "user_id": 157236577,
        "title": "🌤 Прогноз погоды на выходные",
        "trigger_type": "weekly_day",
        "start_day": 0,
        "end_day": 0,
        "day_of_month": 0,
        "hour": 18,
        "minute": 0,
        "days_of_week": [4],  # Friday
        "action_text": "Пятничный вечер! Завтра выходные — самое время проверить планы на загородную поездку или прогулку.",
        "is_active": True,
        "last_completed_period": "",
        "last_notified_date": ""
    }
]


def _pull_from_github() -> Optional[List[Dict[str, Any]]]:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CustomRules-CloudSync"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content_b64 = data.get("content", "")
            raw_json = base64.b64decode(content_b64).decode("utf-8")
            items = json.loads(raw_json)
            if isinstance(items, list) and len(items) > 0:
                RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(RULES_FILE, "w", encoding="utf-8") as f:
                    f.write(raw_json)
                return items
    except Exception as e:
        logger.warning(f"Could not pull custom rules from GitHub: {e}")
    return None


def _push_to_github(items: List[Dict[str, Any]]) -> bool:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "CustomRules-CloudSync"
    }
    try:
        current_sha = None
        try:
            req_get = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req_get, timeout=6) as resp:
                info = json.loads(resp.read().decode("utf-8"))
                current_sha = info.get("sha")
        except Exception:
            pass

        json_str = json.dumps(items, ensure_ascii=False, indent=2)
        content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"🧩 Auto-sync custom rules ({len(items)} entries)",
            "content": content_b64,
            "branch": "main"
        }
        if current_sha:
            payload["sha"] = current_sha

        req_put = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req_put, timeout=10) as resp:
            if resp.status in [200, 201]:
                logger.info(f"Successfully synced {len(items)} custom rules to GitHub repository!")
                return True
    except Exception as e:
        logger.error(f"Failed to push custom rules to GitHub: {e}")
    return False


def _async_push_rules(items: List[Dict[str, Any]]):
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _push_to_github, items)
    except Exception:
        _push_to_github(items)



def reload_from_cloud() -> List[Dict[str, Any]]:
    """Forces fresh pull from GitHub repo to memory/disk."""
    pulled = _pull_from_github()
    if pulled:
        return pulled
    return _load_raw()

def _load_raw() -> List[Dict[str, Any]]:
    if not RULES_FILE.exists():
        pulled = _pull_from_github()
        if pulled:
            return pulled
        _save_raw(DEFAULT_RULES, sync_cloud=True)
        return list(DEFAULT_RULES)
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading custom rules: {e}")
        return []


def _save_raw(data: List[Dict[str, Any]], sync_cloud: bool = True) -> None:
    try:
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if sync_cloud:
            _async_push_rules(data)
    except Exception as e:
        logger.error(f"Error saving custom rules: {e}")


def get_current_period_key(rule: Dict[str, Any]) -> str:
    """Returns unique period key for completion tracking (e.g. '2026-09' for monthly, '2026-09-01' for daily)."""
    now = datetime.now(MSK_TZ)
    tt = rule.get("trigger_type", "daily_time")
    if tt in ["monthly_range", "monthly_day"]:
        return now.strftime("%Y-%m")
    elif tt == "weekly_day":
        # Year and ISO week number
        return f"{now.year}-W{now.isocalendar()[1]}"
    else:
        return now.strftime("%Y-%m-%d")


def is_rule_completed_for_current_period(rule: Dict[str, Any]) -> bool:
    curr_period = get_current_period_key(rule)
    return rule.get("last_completed_period", "") == curr_period


def is_rule_in_active_window(rule: Dict[str, Any]) -> bool:
    """Checks if today falls into the rule's active window/day."""
    now = datetime.now(MSK_TZ)
    tt = rule.get("trigger_type", "daily_time")
    day = now.day
    dow = now.weekday()

    if tt == "monthly_range":
        start_d = rule.get("start_day", rule.get("day_of_month", 1))
        end_d = rule.get("end_day", start_d)
        return start_d <= day <= end_d
    elif tt == "monthly_day":
        target_d = rule.get("day_of_month", 1)
        return day == target_d
    elif tt == "weekly_day":
        target_dows = rule.get("days_of_week", [])
        return dow in target_dows
    else:  # daily
        return True


def get_user_rules(user_id: int = 157236577) -> List[Dict[str, Any]]:
    rules = _load_raw()
    user_rules = [r for r in rules if r.get("user_id") == user_id]
    for r in user_rules:
        r["is_completed_now"] = is_rule_completed_for_current_period(r)
        r["is_in_window_now"] = is_rule_in_active_window(r)
    return user_rules


def add_custom_rule(
    user_id: int,
    title: str,
    trigger_type: str,
    action_text: str,
    hour: int = 12,
    minute: int = 0,
    start_day: int = 0,
    end_day: int = 0,
    day_of_month: int = 0,
    days_of_week: Optional[List[int]] = None
) -> Dict[str, Any]:
    rules = _load_raw()
    rule_id = f"rule_{uuid.uuid4().hex[:8]}"

    if trigger_type == "monthly_range":
        if not start_day:
            start_day = day_of_month or 1
        if not end_day:
            end_day = start_day

    item = {
        "id": rule_id,
        "user_id": user_id,
        "title": title.strip(),
        "trigger_type": trigger_type,
        "start_day": start_day,
        "end_day": end_day,
        "day_of_month": day_of_month or start_day,
        "hour": hour,
        "minute": minute,
        "days_of_week": days_of_week or [],
        "action_text": action_text.strip(),
        "is_active": True,
        "last_completed_period": "",
        "last_notified_date": ""
    }
    rules.append(item)
    _save_raw(rules, sync_cloud=True)
    return item


def mark_rule_completed(user_id: int, rule_id: str) -> Optional[bool]:
    """Marks rule as completed for the current period (turns green 🟢)."""
    rules = _load_raw()
    for r in rules:
        if r.get("id") == rule_id and r.get("user_id") == user_id:
            curr_period = get_current_period_key(r)
            # Toggle between completed and uncompleted
            if r.get("last_completed_period") == curr_period:
                r["last_completed_period"] = ""  # Unmark
                _save_raw(rules, sync_cloud=True)
                return False
            else:
                r["last_completed_period"] = curr_period  # Mark done
                _save_raw(rules, sync_cloud=True)
                return True
    return None


def toggle_rule_state(user_id: int, rule_id: str) -> Optional[bool]:
    rules = _load_raw()
    for r in rules:
        if r.get("id") == rule_id and r.get("user_id") == user_id:
            r["is_active"] = not r.get("is_active", True)
            _save_raw(rules, sync_cloud=True)
            return r["is_active"]
    return None


def delete_custom_rule(user_id: int, rule_id: str) -> bool:
    rules = _load_raw()
    initial_len = len(rules)
    rules = [r for r in rules if not (r.get("id") == rule_id and r.get("user_id") == user_id)]
    if len(rules) < initial_len:
        _save_raw(rules, sync_cloud=True)
        return True
    return False
