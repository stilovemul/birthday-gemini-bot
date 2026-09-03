import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR

logger = logging.getLogger("GeoGastroStorage")
HISTORY_FILE = DATA_DIR / "geo_gastro_history.json"

# In-memory cache {user_id: {"seen_places": [...], "last_lat": float, "last_lon": float, "last_address": str, "last_query": str, "last_category": str}}
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
            logger.error(f"Error loading geo gastro history: {e}")
            _memory_cache = {}
    _loaded = True


def _save_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving geo gastro history: {e}")


def get_user_gastro_context(user_id: int) -> Dict[str, Any]:
    """Returns the full gastro context for user."""
    _load_history()
    return _memory_cache.get(user_id, {
        "seen_places": [],
        "last_lat": None,
        "last_lon": None,
        "last_address": "",
        "last_query": "",
        "last_category": "all"
    })


def save_user_gastro_context(
    user_id: int,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    address: Optional[str] = None,
    query: Optional[str] = None,
    category: Optional[str] = None
):
    """Updates user last search location and query parameters."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {
            "seen_places": [],
            "last_lat": None,
            "last_lon": None,
            "last_address": "",
            "last_query": "",
            "last_category": "all"
        }
    
    ctx = _memory_cache[user_id]
    if lat is not None:
        ctx["last_lat"] = float(lat)
    if lon is not None:
        ctx["last_lon"] = float(lon)
    if address is not None:
        ctx["last_address"] = address
    if query is not None:
        ctx["last_query"] = query
    if category is not None:
        ctx["last_category"] = category
        
    _save_history()


def get_seen_places(user_id: int) -> List[str]:
    """Returns a list of restaurant/bar names already seen by user."""
    ctx = get_user_gastro_context(user_id)
    return list(ctx.get("seen_places", []))


def add_seen_places(user_id: int, places: List[Dict[str, Any]]):
    """Records seen places to avoid duplicates in future recommendations."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {
            "seen_places": [],
            "last_lat": None,
            "last_lon": None,
            "last_address": "",
            "last_query": "",
            "last_category": "all"
        }
    
    seen = _memory_cache[user_id].setdefault("seen_places", [])
    for p in places:
        name = str(p.get("name", "")).strip()
        if name and name not in seen:
            seen.append(name)
            
    if len(seen) > 50:
        _memory_cache[user_id]["seen_places"] = seen[-50:]
        
    _save_history()


def save_last_gastro_recommendations(user_id: int, places: List[Dict[str, Any]], summary: str = "", tip: str = ""):
    """Saves full details of the latest recommended places for interactive Q&A follow-up conversation."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {
            "seen_places": [],
            "last_lat": None,
            "last_lon": None,
            "last_address": "",
            "last_query": "",
            "last_category": "all"
        }
    _memory_cache[user_id]["last_places"] = places
    _memory_cache[user_id]["last_summary"] = summary
    _memory_cache[user_id]["last_tip"] = tip
    _memory_cache[user_id]["chat_history"] = []
    _save_history()


def get_last_gastro_recommendations(user_id: int) -> Dict[str, Any]:
    """Retrieves full details of the latest recommended places and chat history."""
    _load_history()
    ctx = _memory_cache.get(user_id, {})
    return {
        "places": ctx.get("last_places", []),
        "summary": ctx.get("last_summary", ""),
        "tip": ctx.get("last_tip", ""),
        "chat_history": ctx.get("chat_history", [])
    }


def add_gastro_chat_turn(user_id: int, role: str, text: str):
    """Appends a user or assistant message to the interactive gastro dialogue history."""
    _load_history()
    if user_id in _memory_cache:
        history = _memory_cache[user_id].setdefault("chat_history", [])
        history.append({"role": role, "text": text})
        if len(history) > 10:
            _memory_cache[user_id]["chat_history"] = history[-10:]
        _save_history()

