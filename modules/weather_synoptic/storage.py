import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("WeatherStorage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
WEATHER_FILE = os.path.join(DATA_DIR, "weather_config.json")


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_weather_configs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    if not os.path.exists(WEATHER_FILE):
        return {}
    try:
        with open(WEATHER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading weather config: {e}")
        return {}


def save_weather_configs(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(WEATHER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving weather config: {e}")


def get_user_weather_config(user_id: int) -> Dict[str, Any]:
    configs = load_weather_configs()
    return configs.get(str(user_id), {
        "city": "Санкт-Петербург",
        "lat": 59.9386,
        "lon": 30.3141,
        "alerts_enabled": True,
        "last_alert_time": 0
    })


def set_user_weather_config(
    user_id: int,
    city: str,
    lat: float,
    lon: float,
    alerts_enabled: bool = True
) -> Dict[str, Any]:
    configs = load_weather_configs()
    uid = str(user_id)
    curr = configs.get(uid, {})
    curr.update({
        "city": city,
        "lat": lat,
        "lon": lon,
        "alerts_enabled": alerts_enabled
    })
    configs[uid] = curr
    save_weather_configs(configs)
    return curr


def update_user_alert_timestamp(user_id: int, timestamp: float) -> None:
    configs = load_weather_configs()
    uid = str(user_id)
    if uid in configs:
        configs[uid]["last_alert_time"] = timestamp
        save_weather_configs(configs)
