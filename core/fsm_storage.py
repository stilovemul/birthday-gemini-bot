import os
import json
import logging
import threading
from typing import Dict, Any, Optional
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from core.config import DATA_DIR

logger = logging.getLogger("JsonFsmStorage")

FSM_FILE = DATA_DIR / "fsm_states.json"
_lock = threading.RLock()


class JsonFsmStorage(BaseStorage):
    """
    Persistent JSON-backed FSM Storage for aiogram 3.x.
    Persists user states and state data across process restarts, deployments, and reboots.
    """
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        with _lock:
            if FSM_FILE.exists():
                try:
                    with open(FSM_FILE, "r", encoding="utf-8") as f:
                        saved = json.load(f)
                        if isinstance(saved, dict):
                            self._data = saved
                            logger.info(f"Loaded {len(self._data)} FSM user states from disk.")
                except Exception as e:
                    logger.error(f"Error loading fsm_states.json: {e}")
            else:
                self._data = {}

    def _save(self) -> None:
        with _lock:
            try:
                FSM_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(FSM_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error saving fsm_states.json: {e}")

    def _get_key(self, key: StorageKey) -> str:
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        k = self._get_key(key)
        with _lock:
            if k not in self._data:
                self._data[k] = {"state": None, "data": {}}
            state_val = state.state if hasattr(state, "state") else state
            self._data[k]["state"] = state_val
            self._save()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        k = self._get_key(key)
        with _lock:
            entry = self._data.get(k)
            return entry.get("state") if entry else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        k = self._get_key(key)
        with _lock:
            if k not in self._data:
                self._data[k] = {"state": None, "data": {}}
            self._data[k]["data"] = data
            self._save()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        k = self._get_key(key)
        with _lock:
            entry = self._data.get(k)
            return dict(entry.get("data", {})) if entry else {}

    async def close(self) -> None:
        pass
