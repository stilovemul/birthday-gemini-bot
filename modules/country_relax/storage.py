import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR

logger = logging.getLogger("CountryRelaxStorage")
HISTORY_FILE = DATA_DIR / "country_history.json"

# In-memory cache {user_id: {"seen_resorts": [...], "last_query": "...", "last_category": "..."}}
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
            logger.error(f"Error loading country relax history: {e}")
            _memory_cache = {}
    _loaded = True


def _save_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving country relax history: {e}")


def get_seen_resorts(user_id: int) -> List[str]:
    """Возвращает список названий баз/отелей, уже показанных пользователю."""
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return list(user_data.get("seen_resorts", []))


def add_seen_resort(user_id: int, resort_name: str):
    """Добавляет базу в список просмотренных, чтобы исключить повторы."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_resorts": [], "last_query": "", "last_category": "general"}

    clean_name = resort_name.strip()
    seen = _memory_cache[user_id].setdefault("seen_resorts", [])
    if clean_name not in seen:
        seen.append(clean_name)
        if len(seen) > 100:
            _memory_cache[user_id]["seen_resorts"] = seen[-100:]
        _save_history()


def clear_seen_resorts(user_id: int):
    """Сбрасывает список просмотренных баз (когда все уже были показаны)."""
    _load_history()
    if user_id in _memory_cache:
        _memory_cache[user_id]["seen_resorts"] = []
        _save_history()


def set_user_last_country(user_id: int, query: str, category: str = "general"):
    """Сохраняет последний контекст поиска пользователя."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_resorts": [], "last_query": query, "last_category": category}
    else:
        _memory_cache[user_id]["last_query"] = query
        _memory_cache[user_id]["last_category"] = category
    _save_history()


def get_user_last_country(user_id: int) -> Dict[str, str]:
    """Возвращает последний контекст поиска пользователя."""
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return {
        "query": user_data.get("last_query", "Лучший загородный отдых в Ленобласти"),
        "category": user_data.get("last_category", "general")
    }


def save_last_country_resort(user_id: int, resort: Dict[str, Any]):
    """Сохраняет полные данные последней показанной загородной базы для интерактивного диалога и ответов на вопросы."""
    _load_history()
    if user_id not in _memory_cache:
        _memory_cache[user_id] = {"seen_resorts": [], "last_query": "", "last_category": "general"}
    _memory_cache[user_id]["last_resort"] = resort
    _memory_cache[user_id]["chat_history"] = []
    _save_history()


def get_last_country_resort(user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает полные данные последней показанной базы отдыха."""
    _load_history()
    user_data = _memory_cache.get(user_id, {})
    return user_data.get("last_resort")


def add_country_chat_turn(user_id: int, role: str, text: str):
    """Сохраняет сообщение пользователя или консьержа в историю диалога по загородному отдыху."""
    _load_history()
    if user_id in _memory_cache:
        history = _memory_cache[user_id].setdefault("chat_history", [])
        history.append({"role": role, "text": text})
        if len(history) > 10:
            _memory_cache[user_id]["chat_history"] = history[-10:]
        _save_history()

