import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("VKStorage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
VK_FILE = os.path.join(DATA_DIR, "vk_config.json")

DEFAULT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "157236577": {
        "token": "vk1.a.DnpkcFvy--4UQiAXZzzozcY1hyhA36JcaeUid5g_d3Wnc9jMVD5rZEGR1drEfmHAzHutj43asT9Rka9DjInDE1In1POW1hHb18UnUUY47dwKrPhLQ7p3f5v7T8njuxFSx4iDsnghgLrQse42TZRYOSD2kZ9UcnEks_Wy07THJJlQCC1bcWBbnYRzcS5UPuZ4YOXGXitruhA2DfizXSsa4A",
        "user_id_vk": "14058069",
        "user_name": "Олег Уринев",
        "enabled": True,
        "last_messages": 0,
        "last_notifications": 0,
        "last_friends": 0,
        "last_event_ids": []
    }
}


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_vk_configs() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    data = dict(DEFAULT_CONFIGS)
    if os.path.exists(VK_FILE):
        try:
            with open(VK_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                data.update(saved)
        except Exception as e:
            logger.error(f"Error loading vk configs: {e}")
    return data


def save_vk_configs(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(VK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving vk configs: {e}")


def get_user_vk_config(user_id: int) -> Optional[Dict[str, Any]]:
    configs = load_vk_configs()
    return configs.get(str(user_id))


def set_user_vk_config(
    user_id: int,
    token: Optional[str] = None,
    user_id_vk: Optional[str] = None,
    enabled: bool = True
) -> Dict[str, Any]:
    configs = load_vk_configs()
    uid = str(user_id)
    curr = configs.get(uid, {
        "token": "",
        "user_id_vk": "",
        "enabled": True,
        "last_messages": 0,
        "last_notifications": 0,
        "last_friends": 0,
        "last_event_ids": []
    })

    if token is not None:
        curr["token"] = token.strip()
    if user_id_vk is not None:
        curr["user_id_vk"] = user_id_vk.strip()
    curr["enabled"] = enabled

    configs[uid] = curr
    save_vk_configs(configs)
    logger.info(f"Updated VK config for user {user_id}")
    return curr


def update_vk_state(
    user_id: int,
    messages_count: int,
    notifications_count: int,
    friends_count: int = 0,
    new_event_ids: Optional[list] = None
) -> None:
    configs = load_vk_configs()
    uid = str(user_id)
    if uid in configs:
        configs[uid]["last_messages"] = messages_count
        configs[uid]["last_notifications"] = notifications_count
        configs[uid]["last_friends"] = friends_count
        if new_event_ids is not None:
            configs[uid]["last_event_ids"] = new_event_ids[-50:]
        save_vk_configs(configs)
