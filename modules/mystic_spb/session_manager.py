"""
Управление активными сессиями пеших экскурсий по Санкт-Петербургу.
Сохраняет состояние прохождения маршрута (текущая точка, история, статус)
в локальную базу data/spb_tour_sessions.json с защитой от сбоев.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from core.config import DATA_DIR, MSK_TZ

logger = logging.getLogger("MysticSPBSessionManager")
SESSIONS_FILE = os.path.join(DATA_DIR, "spb_tour_sessions.json")


def _load_all_sessions() -> Dict[str, Any]:
    if not os.path.exists(SESSIONS_FILE):
        return {}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading tour sessions from {SESSIONS_FILE}: {e}")
        return {}


def _save_all_sessions(data: Dict[str, Any]) -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving tour sessions to {SESSIONS_FILE}: {e}")


def start_tour_session(user_id: int, tour: Dict[str, Any]) -> Dict[str, Any]:
    """Начинает новую сессию пешей экскурсии."""
    sessions = _load_all_sessions()
    now_str = datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S")

    session = {
        "user_id": user_id,
        "tour": tour,
        "current_stop_idx": 0,
        "status": "active",
        "started_at": now_str,
        "visited_stops": [0]
    }
    sessions[str(user_id)] = session
    _save_all_sessions(sessions)
    logger.info(f"Started tour '{tour.get('title')}' for user {user_id}")
    return session


def get_active_tour_session(user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает текущую активную сессию экскурсии, если она есть."""
    sessions = _load_all_sessions()
    sess = sessions.get(str(user_id))
    if sess and sess.get("status") == "active":
        return sess
    return None


def advance_tour_session(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Переходит к следующей точке экскурсии.
    Если точек больше нет, переводит сессию в статус 'finished'.
    """
    sessions = _load_all_sessions()
    sess = sessions.get(str(user_id))
    if not sess or sess.get("status") != "active":
        return None

    tour = sess.get("tour", {})
    stops = tour.get("stops", [])
    current_idx = sess.get("current_stop_idx", 0)

    if current_idx + 1 < len(stops):
        sess["current_stop_idx"] = current_idx + 1
        visited = sess.get("visited_stops", [])
        if sess["current_stop_idx"] not in visited:
            visited.append(sess["current_stop_idx"])
        sess["visited_stops"] = visited
    else:
        sess["status"] = "finished"
        sess["finished_at"] = datetime.now(MSK_TZ).strftime("%Y-%m-%d %H:%M:%S")

    sessions[str(user_id)] = sess
    _save_all_sessions(sessions)
    return sess


def cancel_tour_session(user_id: int) -> bool:
    """Завершает или отменяет текущую экскурсию."""
    sessions = _load_all_sessions()
    if str(user_id) in sessions:
        sessions[str(user_id)]["status"] = "cancelled"
        _save_all_sessions(sessions)
        return True
    return False


def get_current_stop(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Возвращает данные текущей остановки."""
    tour = session.get("tour", {})
    stops = tour.get("stops", [])
    idx = session.get("current_stop_idx", 0)
    if 0 <= idx < len(stops):
        return stops[idx]
    return None


def get_next_stop(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Возвращает данные следующей остановки, если она есть."""
    tour = session.get("tour", {})
    stops = tour.get("stops", [])
    idx = session.get("current_stop_idx", 0) + 1
    if 0 <= idx < len(stops):
        return stops[idx]
    return None
