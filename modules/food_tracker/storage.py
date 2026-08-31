import json
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("FoodStorage")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
FOOD_FILE = os.path.join(DATA_DIR, "food_logs.json")
GOALS_FILE = os.path.join(DATA_DIR, "food_goals.json")


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def _load_food_data() -> Dict[str, List[Dict[str, Any]]]:
    _ensure_data_dir()
    if not os.path.exists(FOOD_FILE):
        return {}
    try:
        with open(FOOD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading food logs: {e}")
        return {}


def _save_food_data(data: Dict[str, List[Dict[str, Any]]]) -> None:
    _ensure_data_dir()
    try:
        with open(FOOD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving food logs: {e}")


def _load_goals() -> Dict[str, int]:
    _ensure_data_dir()
    if not os.path.exists(GOALS_FILE):
        return {}
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_goals(goals: Dict[str, int]) -> None:
    _ensure_data_dir()
    try:
        with open(GOALS_FILE, "w", encoding="utf-8") as f:
            json.dump(goals, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving food goals: {e}")


def get_user_calorie_goal(user_id: int) -> int:
    goals = _load_goals()
    return goals.get(str(user_id), 2200)


def set_user_calorie_goal(user_id: int, goal_kcal: int) -> None:
    goals = _load_goals()
    goals[str(user_id)] = max(500, min(10000, goal_kcal))
    _save_goals(goals)


def log_meal(
    user_id: int,
    dish_name: str,
    calories: int,
    protein: float,
    fat: float,
    carbs: float,
    weight_g: Optional[int] = None,
    breakdown_text: str = ""
) -> Dict[str, Any]:
    data = _load_food_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []

    now = datetime.now()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "dish_name": dish_name,
        "calories": int(calories),
        "protein": round(float(protein), 1),
        "fat": round(float(fat), 1),
        "carbs": round(float(carbs), 1),
        "weight_g": weight_g,
        "breakdown": breakdown_text
    }
    data[uid].append(entry)
    _save_food_data(data)
    logger.info(f"Logged meal for user {user_id}: {dish_name} ({calories} kcal)")
    return entry


def get_daily_summary(user_id: int, target_date: Optional[str] = None) -> Dict[str, Any]:
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    data = _load_food_data()
    uid = str(user_id)
    user_meals = data.get(uid, [])

    today_meals = [m for m in user_meals if m.get("date") == target_date]
    total_kcal = sum(m.get("calories", 0) for m in today_meals)
    total_p = sum(m.get("protein", 0) for m in today_meals)
    total_f = sum(m.get("fat", 0) for m in today_meals)
    total_c = sum(m.get("carbs", 0) for m in today_meals)
    goal = get_user_calorie_goal(user_id)

    return {
        "date": target_date,
        "meals": today_meals,
        "total_calories": total_kcal,
        "total_protein": round(total_p, 1),
        "total_fat": round(total_f, 1),
        "total_carbs": round(total_c, 1),
        "goal_calories": goal,
        "remaining_calories": max(0, goal - total_kcal)
    }


def delete_meal(user_id: int, meal_id: str) -> bool:
    data = _load_food_data()
    uid = str(user_id)
    if uid in data:
        initial_len = len(data[uid])
        data[uid] = [m for m in data[uid] if m.get("id") != meal_id]
        if len(data[uid]) < initial_len:
            _save_food_data(data)
            return True
    return False


def clear_today_meals(user_id: int) -> int:
    data = _load_food_data()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if uid in data:
        today_count = sum(1 for m in data[uid] if m.get("date") == today)
        data[uid] = [m for m in data[uid] if m.get("date") != today]
        _save_food_data(data)
        return today_count
    return 0
