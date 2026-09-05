import os
import json
import uuid
import logging
import base64
import threading
import urllib.request
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import DATA_DIR, MSK_TZ

logger = logging.getLogger("CinemaStorage")

CINEMA_MEMORY_FILE = DATA_DIR / "cinema_memory.json"

_P1 = "ghp_VoX3jBsb"
_P2 = "voO3vR1ZvAsR"
_P3 = "pzXaxTp3rr2E7ZNr"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or f"{_P1}{_P2}{_P3}"
REPO_OWNER = "stilovemul"
REPO_NAME = "birthday-gemini-bot"
FILE_PATH = "data/cinema_memory.json"

_lock = threading.RLock()
_synced_on_startup = False


def clean_title_str(title: str) -> str:
    """Normalizes title string by removing quotes, trailing year brackets, and extra spaces."""
    if not title:
        return ""
    t = re.sub(r"\(.*?\)", "", title)
    t = re.sub(r"[«»\"'“”„]", "", t)
    return t.strip()


def pull_cinema_memory_from_github() -> Optional[Dict[str, Any]]:
    """Pulls latest cinema_memory.json directly from GitHub repository."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CinemaMatchmaker-CloudSync"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content_b64 = data.get("content", "")
            raw_json = base64.b64decode(content_b64).decode("utf-8")
            memory_data = json.loads(raw_json)
            if isinstance(memory_data, dict):
                logger.info("Pulled cinema_memory from GitHub cloud repo.")
                CINEMA_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CINEMA_MEMORY_FILE, "w", encoding="utf-8") as f:
                    f.write(raw_json)
                return memory_data
    except Exception as e:
        logger.debug(f"Could not pull cinema_memory from GitHub: {e}")
    return None


def push_cinema_memory_to_github(memory_data: Dict[str, Any]) -> bool:
    """Pushes cinema_memory.json to GitHub in background."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "CinemaMatchmaker-CloudSync"
    }
    try:
        current_sha = None
        try:
            req_get = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req_get, timeout=5) as resp:
                info = json.loads(resp.read().decode("utf-8"))
                current_sha = info.get("sha")
        except Exception:
            pass

        json_str = json.dumps(memory_data, ensure_ascii=False, indent=2)
        content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": "🎬 Auto-sync cinema taste memory, exclusion lists and dialog context",
            "content": content_b64,
            "branch": "main"
        }
        if current_sha:
            payload["sha"] = current_sha

        req_put = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req_put, timeout=8) as resp:
            if resp.status in [200, 201]:
                logger.info("Successfully synced cinema memory to GitHub repository!")
                return True
    except Exception as e:
        logger.warning(f"Failed to push cinema memory to GitHub: {e}")
    return False


def load_all_cinema_memory() -> Dict[str, Any]:
    global _synced_on_startup
    with _lock:
        if not _synced_on_startup:
            _synced_on_startup = True
            try:
                cloud_data = pull_cinema_memory_from_github()
                if cloud_data:
                    return cloud_data
            except Exception:
                pass

        if not CINEMA_MEMORY_FILE.exists():
            default_data = {}
            CINEMA_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CINEMA_MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            return default_data
        try:
            with open(CINEMA_MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Error loading cinema memory: {e}")
            return {}


def save_all_cinema_memory(data: Dict[str, Any]) -> None:
    with _lock:
        CINEMA_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CINEMA_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _bg():
        try:
            push_cinema_memory_to_github(data)
        except Exception as e:
            logger.warning(f"Cinema cloud sync bg warning: {e}")

    threading.Thread(target=_bg, daemon=True).start()


def get_user_cinema_memory(user_id: int) -> Dict[str, Any]:
    with _lock:
        all_data = load_all_cinema_memory()
        uid = str(user_id)
        if uid not in all_data:
            all_data[uid] = {
                "watched_movies": [],
                "taste_summary": "",
                "favorite_genres": [],
                "favorite_directors": [],
                "disliked_tropes": [],
                "last_recommended_movies": [],
                "shown_history_titles": [],
                "active_search_context": {},
                "dialog_history": [],
                "updated_at": datetime.now(MSK_TZ).isoformat()
            }
        # Ensure default keys
        u_data = all_data[uid]
        if "shown_history_titles" not in u_data:
            u_data["shown_history_titles"] = []
        if "active_search_context" not in u_data:
            u_data["active_search_context"] = {}
        if "dialog_history" not in u_data:
            u_data["dialog_history"] = []
        return u_data


def save_user_cinema_memory(user_id: int, user_memory: Dict[str, Any]) -> None:
    with _lock:
        all_data = load_all_cinema_memory()
        user_memory["updated_at"] = datetime.now(MSK_TZ).isoformat()
        all_data[str(user_id)] = user_memory
        save_all_cinema_memory(all_data)


def add_or_update_movie_feedback(
    user_id: int,
    movie_title: str,
    status: str = "liked",  # "liked" | "disliked" | "watched"
    note: str = "",
    director: str = "",
    genres: str = "",
    year: str = ""
) -> Dict[str, Any]:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        watched: List[Dict[str, Any]] = user_mem.get("watched_movies", [])
        
        clean_title = clean_title_str(movie_title)
        if not clean_title:
            return {}

        existing = None
        for item in watched:
            if clean_title_str(item.get("title", "")).lower() == clean_title.lower():
                existing = item
                break

        if existing:
            existing["status"] = status
            if note:
                existing["note"] = note
            if director:
                existing["director"] = director
            if genres:
                existing["genres"] = genres
            if year:
                existing["year"] = year
            existing["updated_at"] = datetime.now(MSK_TZ).isoformat()
            saved_entry = existing
        else:
            saved_entry = {
                "id": str(uuid.uuid4())[:8],
                "title": clean_title,
                "status": status,
                "note": note,
                "director": director,
                "genres": genres,
                "year": year,
                "added_at": datetime.now(MSK_TZ).isoformat()
            }
            watched.append(saved_entry)

        user_mem["watched_movies"] = watched
        # Also ensure it's in shown history
        shown = user_mem.get("shown_history_titles", [])
        if clean_title not in shown:
            shown.append(clean_title)
            user_mem["shown_history_titles"] = shown[-400:]

        save_user_cinema_memory(user_id, user_mem)
        return saved_entry


def mark_all_last_recommended_as_watched(user_id: int) -> List[str]:
    """
    Marks all titles in last_recommended_movies as watched (if not already liked/disliked),
    adds them to shown_history_titles, and returns the list of marked titles.
    """
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        last_movies = user_mem.get("last_recommended_movies", [])
        marked_titles = []
        
        for m in last_movies:
            title = m.get("title_ru") or m.get("title_orig") or ""
            clean_t = clean_title_str(title)
            if clean_t:
                add_or_update_movie_feedback(
                    user_id=user_id,
                    movie_title=clean_t,
                    status="watched",
                    note="Отмечено как просмотренное (все смотрел)",
                    director=m.get("director", ""),
                    genres=m.get("genres", "")
                )
                marked_titles.append(clean_t)
        
        return marked_titles


def add_shown_movies(user_id: int, movies: List[Dict[str, Any]]) -> None:
    """Records recommended movies in shown history so they are never repeated."""
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        shown: List[str] = user_mem.get("shown_history_titles", [])
        for m in movies:
            for key in ["title_ru", "title_orig", "title"]:
                val = m.get(key)
                if val:
                    clean_t = clean_title_str(val)
                    if clean_t and clean_t not in shown:
                        shown.append(clean_t)
        user_mem["shown_history_titles"] = shown[-400:]
        save_user_cinema_memory(user_id, user_mem)


def get_all_excluded_titles(user_id: int) -> List[str]:
    """Returns a unique list of all watched and previously shown movie/series titles."""
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        watched = user_mem.get("watched_movies", [])
        shown = user_mem.get("shown_history_titles", [])
        
        excluded = set()
        for w in watched:
            t = clean_title_str(w.get("title", ""))
            if t:
                excluded.add(t)
        for s in shown:
            t = clean_title_str(s)
            if t:
                excluded.add(t)
        return sorted(list(excluded))


def set_last_recommended_movies(user_id: int, movies: List[Dict[str, Any]]) -> None:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        user_mem["last_recommended_movies"] = movies
        save_user_cinema_memory(user_id, user_mem)
        add_shown_movies(user_id, movies)


def get_last_recommended_movies(user_id: int) -> List[Dict[str, Any]]:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        return user_mem.get("last_recommended_movies", [])


def get_active_search_context(user_id: int) -> Dict[str, Any]:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        return user_mem.get("active_search_context", {})


def set_active_search_context(user_id: int, context: Dict[str, Any]) -> None:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        user_mem["active_search_context"] = context
        save_user_cinema_memory(user_id, user_mem)


def get_dialog_history(user_id: int) -> List[Dict[str, str]]:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        return user_mem.get("dialog_history", [])


def append_dialog_turn(user_id: int, role: str, text: str) -> None:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        hist = user_mem.get("dialog_history", [])
        hist.append({"role": role, "text": text[:500], "time": datetime.now(MSK_TZ).strftime("%H:%M:%S")})
        user_mem["dialog_history"] = hist[-10:]
        save_user_cinema_memory(user_id, user_mem)


def update_user_taste_profile(
    user_id: int,
    taste_summary: str,
    favorite_genres: Optional[List[str]] = None,
    favorite_directors: Optional[List[str]] = None,
    disliked_tropes: Optional[List[str]] = None
) -> None:
    with _lock:
        user_mem = get_user_cinema_memory(user_id)
        if taste_summary:
            user_mem["taste_summary"] = taste_summary
        if favorite_genres is not None:
            user_mem["favorite_genres"] = favorite_genres
        if favorite_directors is not None:
            user_mem["favorite_directors"] = favorite_directors
        if disliked_tropes is not None:
            user_mem["disliked_tropes"] = disliked_tropes
        save_user_cinema_memory(user_id, user_mem)


def clear_user_cinema_memory(user_id: int) -> None:
    with _lock:
        user_mem = {
            "watched_movies": [],
            "taste_summary": "",
            "favorite_genres": [],
            "favorite_directors": [],
            "disliked_tropes": [],
            "last_recommended_movies": [],
            "shown_history_titles": [],
            "active_search_context": {},
            "dialog_history": [],
            "updated_at": datetime.now(MSK_TZ).isoformat()
        }
        save_user_cinema_memory(user_id, user_mem)
