import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("Drive2Storage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
CONFIG_FILE = os.path.join(DATA_DIR, "drive2_config.json")

DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "157236577": {
        "profile_url": "https://www.drive2.ru/users/manofftoday/",
        "cookies": "AhQDQVNTVAlxuQCAACF2CN8HSipsA94AAAABNfX8TU0jV5-Mzz1hUWo2boSDXKo",
        "user_name": "Олег (manofftoday)",
        "enabled": True,
        "last_messages": 0,
        "last_notifications": 0,
        "last_event_ids": []
    }
}


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_drive2_configs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    data = dict(DEFAULT_CONFIGS)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                data.update(saved)
        except Exception as e:
            logger.error(f"Error loading drive2 configs: {e}")
    return data


def save_drive2_configs(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving drive2 configs: {e}")


def get_user_drive2_config(user_id: int) -> Optional[Dict[str, Any]]:
    configs = load_drive2_configs()
    return configs.get(str(user_id))


def set_user_drive2_config(
    user_id: int,
    cookies: Optional[str] = None,
    profile_url: Optional[str] = None,
    user_name: Optional[str] = None,
    enabled: bool = True
) -> Dict[str, Any]:
    configs = load_drive2_configs()
    uid = str(user_id)
    curr = configs.get(uid, {
        "profile_url": "",
        "cookies": "",
        "user_name": "",
        "enabled": True,
        "last_messages": 0,
        "last_notifications": 0,
        "last_event_ids": []
    })

    if cookies is not None:
        curr["cookies"] = cookies.strip()
    if profile_url is not None:
        curr["profile_url"] = profile_url.strip()
    if user_name is not None:
        curr["user_name"] = user_name.strip()
    curr["enabled"] = enabled

    configs[uid] = curr
    save_drive2_configs(configs)
    logger.info(f"Updated Drive2 config for user {user_id}")
    return curr


def update_drive2_state(
    user_id: int,
    messages_count: int,
    notifications_count: int,
    new_event_ids: Optional[list] = None
) -> None:
    configs = load_drive2_configs()
    uid = str(user_id)
    if uid in configs:
        configs[uid]["last_messages"] = messages_count
        configs[uid]["last_notifications"] = notifications_count
        if new_event_ids is not None:
            configs[uid]["last_event_ids"] = new_event_ids[-30:]
        save_drive2_configs(configs)
