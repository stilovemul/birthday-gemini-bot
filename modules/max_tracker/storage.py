import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("MAXStorage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
MAX_FILE = os.path.join(DATA_DIR, "max_config.json")

DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "157236577": {
        "token": "",
        "viewer_id": "",
        "user_name": "Олег Уринев",
        "enabled": True,
        "last_messages": 0,
        "last_unread_chats": 0,
        "last_notifications": 0,
        "last_event_ids": []
    }
}


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_max_configs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    data = dict(DEFAULT_CONFIGS)
    if os.path.exists(MAX_FILE):
        try:
            with open(MAX_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                data.update(saved)
        except Exception as e:
            logger.error(f"Error loading max configs: {e}")
    return data


def save_max_configs(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(MAX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving max configs: {e}")


def get_user_max_config(user_id: int) -> Optional[Dict[str, Any]]:
    configs = load_max_configs()
    return configs.get(str(user_id))


def set_user_max_config(
    user_id: int,
    token: Optional[str] = None,
    viewer_id: Optional[str] = None,
    user_name: Optional[str] = None,
    enabled: bool = True
) -> Dict[str, Any]:
    configs = load_max_configs()
    uid = str(user_id)
    curr = configs.get(uid, {
        "token": "",
        "viewer_id": "",
        "user_name": "",
        "enabled": True,
        "last_messages": 0,
        "last_unread_chats": 0,
        "last_notifications": 0,
        "last_event_ids": []
    })

    if token is not None:
        curr["token"] = token.strip()
    if viewer_id is not None:
        curr["viewer_id"] = str(viewer_id).strip()
    if user_name is not None:
        curr["user_name"] = str(user_name).strip()
    curr["enabled"] = enabled

    configs[uid] = curr
    save_max_configs(configs)
    logger.info(f"Updated MAX config for user {user_id}")
    return curr


def update_max_state(
    user_id: int,
    messages_count: int,
    unread_chats_count: int = 0,
    notifications_count: int = 0,
    new_event_ids: Optional[list] = None
) -> None:
    configs = load_max_configs()
    uid = str(user_id)
    if uid in configs:
        configs[uid]["last_messages"] = messages_count
        configs[uid]["last_unread_chats"] = unread_chats_count
        configs[uid]["last_notifications"] = notifications_count
        if new_event_ids is not None:
            configs[uid]["last_event_ids"] = new_event_ids[-50:]
        save_max_configs(configs)
