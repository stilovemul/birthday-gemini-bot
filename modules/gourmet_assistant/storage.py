import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR

logger = logging.getLogger("GourmetStorage")
HISTORY_FILE = DATA_DIR / "gourmet_history.json"

# In-memory cache {user_id: {"seen": {category: [titles]}, "last_category": "...", "last_query": "...", "last_recipe": {...}}}
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
            logger.error(f"Error loading gourmet history: {e}")
            _memory_cache = {}
    _loaded = True


def _save_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving gourmet history: {e}")


def get_seen_recipes(user_id: int, category: str) -> List[str]:
    """Returns a list of dish titles already seen by user in this category."""
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    seen_dict = user_data.get("seen", {})
    return list(seen_dict.get(category, []))


def add_seen_recipe(user_id: int, category: str, title: str, full_data: Optional[Dict[str, Any]] = None):
    """Records a generated recipe to prevent duplicates and saves last recipe for shopping list."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {
            "seen": {},
            "last_category": category,
            "last_query": title,
            "last_recipe": full_data or {}
        }
    
    user_entry = _memory_cache[user_id]
    user_entry["last_category"] = category
    user_entry["last_query"] = title
    if full_data:
        user_entry["last_recipe"] = full_data

    seen_dict = user_entry.setdefault("seen", {})
    cat_list = seen_dict.setdefault(category, [])
    
    clean_title = title.strip()
    if clean_title and clean_title not in cat_list:
        cat_list.append(clean_title)
        if len(cat_list) > 25:
            seen_dict[category] = cat_list[-25:]
    
    _save_history()


def set_user_last_gourmet(user_id: int, category: str, query: str, full_data: Optional[Dict[str, Any]] = None):
    """Saves the last category, query, and recipe data for contextual follow-up / another recipe."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen": {}, "last_category": category, "last_query": query, "last_recipe": {}}
    
    _memory_cache[user_id]["last_category"] = category
    _memory_cache[user_id]["last_query"] = query
    if full_data:
        _memory_cache[user_id]["last_recipe"] = full_data
    _save_history()


def get_user_last_gourmet(user_id: int) -> Dict[str, Any]:
    """Retrieves user's last gourmet category, query, and recipe data."""
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return {
        "category": user_data.get("last_category", "breakfast"),
        "query": user_data.get("last_query", ""),
        "last_recipe": user_data.get("last_recipe", {})
    }


def clear_user_seen(user_id: int, category: Optional[str] = None):
    """Clears history if user wants to reset."""
    _load_history()
    if user_id in _memory_cache:
        if category:
            _memory_cache[user_id].get("seen", {}).pop(category, None)
        else:
            _memory_cache[user_id]["seen"] = {}
        _save_history()
