import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("TravelEnglishStorage")

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "travel_english_stats.json")


def _load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load travel_english_stats.json: {e}")
        return {}


def _save_data(data: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save travel_english_stats.json: {e}")


def get_user_profile(user_id: int) -> Dict[str, Any]:
    """Возвращает профиль пользователя или создает начальный."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "level": "🎒 Начинающий турист (Starter)",
            "quizzes_completed": 0,
            "correct_answers": 0,
            "total_questions": 0,
            "dialogs_count": 0,
            "streak_days": 1,
            "saved_phrases": []
        }
        _save_data(data)
    return data[uid]


def add_user_xp(user_id: int, xp_amount: int, is_correct: bool = True):
    """Начисляет XP и обновляет статистику/уровень."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        get_user_profile(user_id)
        data = _load_data()

    user = data[uid]
    user["xp"] = user.get("xp", 0) + xp_amount
    user["total_questions"] = user.get("total_questions", 0) + 1
    if is_correct:
        user["correct_answers"] = user.get("correct_answers", 0) + 1

    # Расчет уровня по шкале XP
    xp = user["xp"]
    if xp >= 500:
        lvl = "🗽 Свой на Бруклине (Native Walker)"
    elif xp >= 250:
        lvl = "🕶 Street Smart (Бывалый путешественник)"
    elif xp >= 100:
        lvl = "✈️ Уверенный турист (Traveler Pro)"
    elif xp >= 40:
        lvl = "🧳 Разговорный практик (Explorer)"
    else:
        lvl = "🎒 Начинающий турист (Starter)"
    user["level"] = lvl

    _save_data(data)
    return user


def increment_dialogs_count(user_id: int):
    """Увеличивает счетчик диалоговых тренировок."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        get_user_profile(user_id)
        data = _load_data()
    data[uid]["dialogs_count"] = data[uid].get("dialogs_count", 0) + 1
    data[uid]["xp"] = data[uid].get("xp", 0) + 15  # 15 XP за диалог
    _save_data(data)


def save_phrase(user_id: int, phrase: str, translation: str):
    """Сохраняет понравившуюся фразу в блокнот пользователя."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        get_user_profile(user_id)
        data = _load_data()
    saved = data[uid].setdefault("saved_phrases", [])
    entry = {"en": phrase, "ru": translation}
    if entry not in saved:
        saved.append(entry)
        _save_data(data)


def save_dialog_session(
    user_id: int,
    scenario_key: str,
    history: str,
    turns: int,
    last_char_reply_en: str = "",
    last_char_reply_ru: str = "",
    last_suggestions: list = None,
    scenario_info: Optional[Dict[str, Any]] = None
):
    """
    Сохраняет прогресс и историю текущего диалога на диск в data/travel_english_stats.json.
    Диалог никогда не потеряется при выходе в меню или перезапуске бота.
    """
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        get_user_profile(user_id)
        data = _load_data()

    dialogs = data[uid].setdefault("saved_dialogs", {})
    entry = {
        "scenario_key": scenario_key,
        "history": history,
        "turns": turns,
        "last_char_reply_en": last_char_reply_en,
        "last_char_reply_ru": last_char_reply_ru,
        "last_suggestions": last_suggestions or []
    }
    if scenario_info:
        entry["scenario_info"] = scenario_info
    elif scenario_key in dialogs and "scenario_info" in dialogs[scenario_key]:
        entry["scenario_info"] = dialogs[scenario_key]["scenario_info"]

    dialogs[scenario_key] = entry
    data[uid]["last_active_scenario"] = scenario_key
    _save_data(data)


def get_saved_dialog(user_id: int, scenario_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Возвращает сохраненную сессию диалога.
    Если scenario_key не передан — возвращает последний активный незавершенный диалог.
    """
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        return None

    dialogs = data[uid].get("saved_dialogs", {})
    if scenario_key:
        return dialogs.get(scenario_key)

    last_key = data[uid].get("last_active_scenario")
    if last_key and last_key in dialogs:
        session = dialogs[last_key]
        if session.get("turns", 0) > 0:
            return session

    # Поиск любого активного диалога с turns > 0
    for sk, s in dialogs.items():
        if s.get("turns", 0) > 0:
            return s

    return None


def get_all_saved_dialogs(user_id: int) -> Dict[str, Any]:
    """Возвращает словарь всех сохраненных сессий пользователя."""
    data = _load_data()
    uid = str(user_id)
    if uid not in data:
        return {}
    return data[uid].get("saved_dialogs", {})


def clear_saved_dialog(user_id: int, scenario_key: str):
    """Очищает историю конкретного сценария при нажатии 'Начать сначала'."""
    data = _load_data()
    uid = str(user_id)
    if uid in data and "saved_dialogs" in data[uid]:
        if scenario_key in data[uid]["saved_dialogs"]:
            del data[uid]["saved_dialogs"][scenario_key]
            if data[uid].get("last_active_scenario") == scenario_key:
                data[uid]["last_active_scenario"] = None
            _save_data(data)

