import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("SmartHomeStorage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
CONFIG_FILE = os.path.join(DATA_DIR, "smart_home_config.json")

DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "157236577": {
        "token": "y0__wgBEM62vy8Y8LE8IJz5zNwYMKqdv5oI2nSfCW47tU_SVRXAqc0cwi93l08",
        "user_name": "Олег",
        "enabled": True,
        "last_devices_count": 0
    }
}


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_smart_home_configs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    data = dict(DEFAULT_CONFIGS)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                data.update(saved)
        except Exception as e:
            logger.error(f"Error loading smart home config: {e}")
    return data


def save_smart_home_configs(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving smart home config: {e}")


def get_user_smart_home_config(user_id: int) -> Optional[Dict[str, Any]]:
    configs = load_smart_home_configs()
    return configs.get(str(user_id), DEFAULT_CONFIGS.get("157236577"))


def set_user_smart_home_token(user_id: int, token: str) -> Dict[str, Any]:
    configs = load_smart_home_configs()
    uid = str(user_id)
    curr = configs.get(uid, {"user_name": "Олег", "enabled": True})
    curr["token"] = token.strip()
    curr["enabled"] = True
    configs[uid] = curr
    save_smart_home_configs(configs)
    return curr
