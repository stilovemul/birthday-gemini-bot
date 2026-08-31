import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("Drive2Storage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DRIVE2_FILE = os.path.join(DATA_DIR, "drive2_config.json")


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_drive2_configs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    if not os.path.exists(DRIVE2_FILE):
        return {}
    try:
        with open(DRIVE2_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading drive2 configs: {e}")
        return {}


def save_drive2_configs(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(DRIVE2_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving drive2 configs: {e}")


def get_user_drive2_config(user_id: int) -> Optional[Dict[str, Any]]:
    configs = load_drive2_configs()
    return configs.get(str(user_id))


def set_user_drive2_config(
    user_id: int,
    profile_url: Optional[str] = None,
    cookies: Optional[str] = None,
    enabled: bool = True
) -> Dict[str, Any]:
    configs = load_drive2_configs()
    uid = str(user_id)
    curr = configs.get(uid, {
        "profile_url": "",
        "cookies": "",
        "enabled": True,
        "last_messages": 0,
        "last_notifications": 0,
        "last_followers": 0,
        "last_event_ids": []
    })

    if profile_url is not None:
        curr["profile_url"] = profile_url.strip()
    if cookies is not None:
        curr["cookies"] = cookies.strip()
    curr["enabled"] = enabled

    configs[uid] = curr
    save_drive2_configs(configs)
    logger.info(f"Updated Drive2 config for user {user_id}")
    return curr


def update_drive2_state(
    user_id: int,
    messages_count: int,
    notifications_count: int,
    followers_count: Optional[int] = None,
    new_event_ids: Optional[list] = None
) -> None:
    configs = load_drive2_configs()
    uid = str(user_id)
    if uid in configs:
        configs[uid]["last_messages"] = messages_count
        configs[uid]["last_notifications"] = notifications_count
        if followers_count is not None:
            configs[uid]["last_followers"] = followers_count
        if new_event_ids is not None:
            configs[uid]["last_event_ids"] = new_event_ids[-50:]  # Keep last 50
        save_drive2_configs(configs)
