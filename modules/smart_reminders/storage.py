import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.config import DATA_DIR, MSK_TZ

logger = logging.getLogger("SmartRemindersStorage")
REMINDERS_FILE = DATA_DIR / "reminders.json"


def load_reminders() -> List[Dict[str, Any]]:
    if not REMINDERS_FILE.exists():
        save_reminders([])
        return []
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Error loading reminders: {e}")
        return []


def save_reminders(reminders: List[Dict[str, Any]]) -> None:
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving reminders: {e}")


def add_reminder(
    user_id: int,
    text: str,
    target_dt: datetime,
    target_display: Optional[str] = None,
    *args,
    **kwargs
) -> Dict[str, Any]:
    reminders = load_reminders()
    display = target_display or target_dt.strftime("%d.%m.%Y в %H:%M MSK")
    item = {
        "id": str(uuid.uuid4())[:6],
        "user_id": user_id,
        "text": text.strip(),
        "target_iso": target_dt.isoformat(),
        "target_display": display,
        "status": "pending",
        "created_at": datetime.now(MSK_TZ).isoformat()
    }
    reminders.append(item)
    save_reminders(reminders)
    logger.info(f"Added reminder for user {user_id}: '{text}' at {display}")
    return item


def get_active_reminders(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    reminders = load_reminders()
    items = [r for r in reminders if r.get("status") == "pending"]
    if user_id:
        items = [r for r in items if r.get("user_id") == user_id]
    items.sort(key=lambda x: x.get("target_iso", ""))
    return items


def get_due_reminders() -> List[Dict[str, Any]]:
    reminders = load_reminders()
    now_iso = datetime.now(MSK_TZ).isoformat()
    due = []
    for r in reminders:
        if r.get("status") == "pending" and r.get("target_iso", "") <= now_iso:
            due.append(r)
    return due


def mark_as_done(reminder_id: str) -> None:
    reminders = load_reminders()
    for r in reminders:
        if r.get("id") == reminder_id:
            r["status"] = "done"
            r["done_at"] = datetime.now(MSK_TZ).isoformat()
    save_reminders(reminders)


def delete_reminder(reminder_id: str) -> bool:
    reminders = load_reminders()
    target = reminder_id.strip().lower()
    initial_len = len(reminders)
    reminders = [r for r in reminders if r.get("id", "").lower() != target]
    if len(reminders) < initial_len:
        save_reminders(reminders)
        return True
    return False
