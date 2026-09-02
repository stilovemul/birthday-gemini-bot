import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from core.config import DATA_DIR

logger = logging.getLogger("WeekendStorage")
HISTORY_FILE = DATA_DIR / "weekend_history.json"

# In-memory cache {user_id: {"seen_titles": [...], "last_query": "...", "last_mode": "..."}}
_memory_cache: Dict[int, Dict[str, Any]] = {}
_loaded = False


def _load_history():
    global _memory_cache, _loaded
    if _loaded:
        return
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                _memory_cache = {int(k): v for k, v in raw.items()}
        except Exception as e:
            logger.error(f"Error loading weekend history: {e}")
            _memory_cache = {}
    _loaded = True


def _save_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving weekend history: {e}")


def get_seen_routes(user_id: int) -> List[str]:
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return list(user_data.get("seen_titles", []))


def add_seen_route(user_id: int, title: str):
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_titles": [], "last_query": "", "last_mode": "general"}
    
    clean_title = title.strip()
    seen = _memory_cache[user_id].setdefault("seen_titles", [])
    if clean_title not in seen:
        seen.append(clean_title)
        if len(seen) > 30:
            _memory_cache[user_id]["seen_titles"] = seen[-30:]
        _save_history()


def clear_seen_routes(user_id: int):
    _load_history()
    if user_id in _memory_cache:
        _memory_cache[user_id]["seen_titles"] = []
        _save_history()


def set_user_last_trip(user_id: int, query: str, mode_type: str = "general"):
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_titles": [], "last_query": query, "last_mode": mode_type}
    else:
        _memory_cache[user_id]["last_query"] = query
        _memory_cache[user_id]["last_mode"] = mode_type
    _save_history()


def get_user_last_trip(user_id: int) -> Dict[str, str]:
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return {
        "query": user_data.get("last_query", "Лучший сценарий проведения выходного дня под текущий сезон"),
        "mode": user_data.get("last_mode", "general")
    }
