import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from core.config import MSK_TZ

logger = logging.getLogger("SleepCalculator")

# Average time a healthy person needs to fall asleep (in minutes)
FALL_ASLEEP_MINUTES = 14
# Standard human sleep cycle duration (in minutes)
CYCLE_MINUTES = 90


def calculate_bedtimes_for_wakeup(wake_hour: int, wake_minute: int) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Calculates the exact times to go to bed in order to wake up at (wake_hour:wake_minute)
    fresh and at the end of complete 90-minute sleep cycles.
    """
    now = datetime.now(MSK_TZ)
    # Target wake up time today or tomorrow
    target_wake = now.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
    if target_wake <= now:
        target_wake += timedelta(days=1)

    cycles_info = [
        {"cycles": 6, "hours": 9.0, "quality": "⭐ Идеально (9 ч)", "desc": "Максимальное восстановление, память и иммунитет"},
        {"cycles": 5, "hours": 7.5, "quality": "🌟 Золотой стандарт (7.5 ч)", "desc": "Оптимальная норма взрослого человека"},
        {"cycles": 4, "hours": 6.0, "quality": "✨ Достаточно (6 ч)", "desc": "Хороший уровень энергии без чувства сонливости"},
        {"cycles": 3, "hours": 4.5, "quality": "⚡ Минимум (4.5 ч)", "desc": "Экстренный режим для продуктивности"}
    ]

    results = []
    for info in cycles_info:
        total_sleep_minutes = int(info["cycles"] * CYCLE_MINUTES + FALL_ASLEEP_MINUTES)
        bed_time = target_wake - timedelta(minutes=total_sleep_minutes)
        bed_str = bed_time.strftime("%H:%M")
        results.append({
            "bed_time_str": bed_str,
            "bed_datetime": bed_time,
            "cycles": info["cycles"],
            "hours": info["hours"],
            "quality": info["quality"],
            "desc": info["desc"]
        })

    wake_str = f"{wake_hour:02d}:{wake_minute:02d}"
    return wake_str, results


def calculate_wakeups_from_now() -> Tuple[str, List[Dict[str, Any]]]:
    """
    Calculates wake up times if the user goes to bed RIGHT NOW.
    """
    now = datetime.now(MSK_TZ)
    asleep_time = now + timedelta(minutes=FALL_ASLEEP_MINUTES)

    cycles_info = [
        {"cycles": 6, "hours": 9.0, "quality": "⭐ 6 циклов (9 ч)", "desc": "Полный заряд бодрости и продуктивности"},
        {"cycles": 5, "hours": 7.5, "quality": "🌟 5 циклов (7.5 ч)", "desc": "Идеально для буднего дня"},
        {"cycles": 4, "hours": 6.0, "quality": "✨ 4 цикла (6 ч)", "desc": "Лёгкий подъем без разбитости"},
        {"cycles": 3, "hours": 4.5, "quality": "⚡ 3 цикла (4.5 ч)", "desc": "Быстрый сон на крайний случай"}
    ]

    results = []
    for info in cycles_info:
        wake_time = asleep_time + timedelta(minutes=int(info["cycles"] * CYCLE_MINUTES))
        wake_str = wake_time.strftime("%H:%M")
        results.append({
            "wake_time_str": wake_str,
            "wake_datetime": wake_time,
            "cycles": info["cycles"],
            "hours": info["hours"],
            "quality": info["quality"],
            "desc": info["desc"]
        })

    now_str = now.strftime("%H:%M")
    return now_str, results


def get_power_naps() -> Tuple[str, List[Dict[str, Any]]]:
    """
    Calculates daytime restorative Power Naps from current time.
    """
    now = datetime.now(MSK_TZ)
    naps = [
        {
            "name": "🚀 Power Nap (20 минут)",
            "wake_time": (now + timedelta(minutes=20 + 5)).strftime("%H:%M"),
            "desc": "Быстрая перезагрузка внимания и реакции без перехода в глубокий сон (без вялости)."
        },
        {
            "name": "💡 NASA Nap (26 минут)",
            "wake_time": (now + timedelta(minutes=26 + 5)).strftime("%H:%M"),
            "desc": "Исследование NASA: повышает продуктивность на 34% и концентрацию на 54%."
        },
        {
            "name": "🧠 Full Reboot Nap (90 минут)",
            "wake_time": (now + timedelta(minutes=90 + 10)).strftime("%H:%M"),
            "desc": "Один полный цикл сна. Стимулирует память, творческое мышление и физические силы."
        }
    ]
    return now.strftime("%H:%M"), naps
