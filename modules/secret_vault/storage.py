import json
import os
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("SecretVaultStorage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
VAULT_FILE = os.path.join(DATA_DIR, "vault.json")

# In-memory unlocked sessions: {user_id: unlocked_until_timestamp}
unlocked_sessions: Dict[int, float] = {}
# In-memory state for PIN creation or note adding
user_vault_states: Dict[int, str] = {}


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_vault_data() -> Dict[str, Dict[str, Any]]:
    _ensure_data_dir()
    if not os.path.exists(VAULT_FILE):
        return {}
    try:
        with open(VAULT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading vault data: {e}")
        return {}


def save_vault_data(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_data_dir()
    try:
        with open(VAULT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving vault data: {e}")


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(f"super_salt_vault_{pin}".encode("utf-8")).hexdigest()


def is_vault_initialized(user_id: int) -> bool:
    data = load_vault_data()
    user_data = data.get(str(user_id))
    return bool(user_data and user_data.get("pin_hash"))


def set_user_pin(user_id: int, pin: str) -> None:
    data = load_vault_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"pin_hash": "", "notes": []}
    data[uid]["pin_hash"] = _hash_pin(pin)
    save_vault_data(data)
    # Unlock for 10 minutes upon setting
    unlocked_sessions[user_id] = time.time() + 600
    logger.info(f"PIN set and vault unlocked for user {user_id}")


def verify_pin(user_id: int, pin: str) -> bool:
    data = load_vault_data()
    user_data = data.get(str(user_id))
    if not user_data or not user_data.get("pin_hash"):
        return False
    if user_data["pin_hash"] == _hash_pin(pin):
        unlocked_sessions[user_id] = time.time() + 600  # 10 minutes session
        return True
    return False


def is_vault_unlocked(user_id: int) -> bool:
    expiry = unlocked_sessions.get(user_id, 0)
    return time.time() < expiry


def lock_vault(user_id: int) -> None:
    if user_id in unlocked_sessions:
        del unlocked_sessions[user_id]
    if user_id in user_vault_states:
        del user_vault_states[user_id]


def add_secret_note(user_id: int, title: str, content: str) -> Dict[str, Any]:
    data = load_vault_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"pin_hash": "", "notes": []}

    note_id = str(int(time.time() * 1000))[-6:]
    note = {
        "id": note_id,
        "title": title.strip(),
        "content": content.strip(),
        "created_at": time.strftime("%Y-%m-%d %H:%M")
    }
    data[uid]["notes"].append(note)
    save_vault_data(data)
    return note


def get_secret_notes(user_id: int) -> List[Dict[str, Any]]:
    data = load_vault_data()
    user_data = data.get(str(user_id))
    if not user_data:
        return []
    return user_data.get("notes", [])


def delete_secret_note(user_id: int, note_id: str) -> bool:
    data = load_vault_data()
    uid = str(user_id)
    if uid in data and "notes" in data[uid]:
        orig_len = len(data[uid]["notes"])
        data[uid]["notes"] = [n for n in data[uid]["notes"] if str(n.get("id")) != str(note_id)]
        if len(data[uid]["notes"]) < orig_len:
            save_vault_data(data)
            return True
    return False
