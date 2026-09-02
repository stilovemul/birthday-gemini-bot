import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from core.config import DATA_DIR

logger = logging.getLogger("PhotoSpotsStorage")
HISTORY_FILE = DATA_DIR / "photo_spots_history.json"

# In-memory cache {user_id: {"seen_spots": [...], "last_query": "..."}}
_memory_cache: Dict[int, Dict[str, Any]] = {}
_loaded = False


def _load_history():
    global _memory_cache, _loaded
    if _loaded:
        return
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8-sig") as f:
                raw = json.load(f)
                _memory_cache = {int(k): v for k, v in raw.items()}
        except Exception as e:
            logger.error(f"Error loading photo spots history: {e}")
            _memory_cache = {}
    _loaded = True


def _save_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving photo spots history: {e}")


def get_seen_spots(user_id: int) -> List[str]:
    """Returns a list of spot names already seen by user."""
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return list(user_data.get("seen_spots", []))


def add_seen_spot(user_id: int, spot_name: str):
    """Records a single seen spot to prevent duplicates."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_spots": [], "last_query": ""}
    
    clean_name = spot_name.strip()
    if not clean_name:
        return
    seen = _memory_cache[user_id].setdefault("seen_spots", [])
    if clean_name not in seen:
        seen.append(clean_name)
        if len(seen) > 40:
            _memory_cache[user_id]["seen_spots"] = seen[-40:]
        _save_history()


def add_seen_spots(user_id: int, spot_names: List[str]):
    """Records multiple spots into seen history."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_spots": [], "last_query": ""}
    
    seen = _memory_cache[user_id].setdefault("seen_spots", [])
    changed = False
    for s in spot_names:
        clean = s.strip()
        if clean and clean not in seen:
            seen.append(clean)
            changed = True
    if changed:
        if len(seen) > 40:
            _memory_cache[user_id]["seen_spots"] = seen[-40:]
        _save_history()


def get_last_query(user_id: int) -> str:
    """Returns the user's last photo spots query or preset."""
    _load_history()
    return _memory_cache.get(user_id, {}).get("last_query", "Кинематографичные фотолокации Санкт-Петербурга")


def set_last_query(user_id: int, query: str):
    """Saves the user's last query."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_spots": [], "last_query": ""}
    _memory_cache[user_id]["last_query"] = query.strip()
    _save_history()


def clear_seen_spots(user_id: int):
    """Clears viewed spots history for the user."""
    _load_history()
    if user_id in _memory_cache:
        _memory_cache[user_id]["seen_spots"] = []
        _save_history()