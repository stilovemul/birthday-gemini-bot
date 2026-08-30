import json
import re
import uuid
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from core.config import BIRTHDAYS_FILE, MSK_TZ

MONTHS_RU = {
    "января": 1, "январь": 1, "янв": 1,
    "февраля": 2, "февраль": 2, "фев": 2,
    "марта": 3, "март": 3, "мар": 3,
    "апреля": 4, "апрель": 4, "апр": 4,
    "мая": 5, "май": 5,
    "июня": 6, "июнь": 6, "июн": 6,
    "июля": 7, "июль": 7, "июл": 7,
    "августа": 8, "август": 8, "авг": 8,
    "сентября": 9, "сентябрь": 9, "сен": 9, "сеп": 9,
    "октября": 10, "октябрь": 10, "окт": 10,
    "ноября": 11, "ноябрь": 11, "ноя": 11,
    "декабря": 12, "декабрь": 12, "дек": 12,
}

MONTH_NAMES_RU = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


def get_current_msk_date() -> date:
    return datetime.now(MSK_TZ).date()


def load_birthdays() -> List[Dict[str, Any]]:
    if not BIRTHDAYS_FILE.exists():
        save_birthdays([])
        return []
    try:
        with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_birthdays(birthdays: List[Dict[str, Any]]) -> None:
    BIRTHDAYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(birthdays, f, ensure_ascii=False, indent=2)


def parse_date_string(date_str: str) -> Optional[Tuple[int, int, Optional[int]]]:
    text = date_str.strip().lower()

    ru_match = re.match(r"^(\d{1,2})\s+([а-яё]+)(?:\s+(\d{2,4}))?$", text)
    if ru_match:
        day = int(ru_match.group(1))
        month_word = ru_match.group(2)
        year_val = int(ru_match.group(3)) if ru_match.group(3) else None
        if month_word in MONTHS_RU:
            month = MONTHS_RU[month_word]
            if year_val and year_val < 100:
                year_val = 1900 + year_val if year_val > 30 else 2000 + year_val
            return _validate_date(day, month, year_val)

    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))
        return _validate_date(day, month, year)

    dot_match = re.match(r"^(\d{1,2})[./\-](\d{1,2})(?:[./\-](\d{2,4}))?$", text)
    if dot_match:
        day = int(dot_match.group(1))
        month = int(dot_match.group(2))
        year_str = dot_match.group(3)
        year = None
        if year_str:
            year = int(year_str)
            if year < 100:
                year = 1900 + year if year > 30 else 2000 + year
        return _validate_date(day, month, year)

    return None


def _validate_date(day: int, month: int, year: Optional[int]) -> Optional[Tuple[int, int, Optional[int]]]:
    if not (1 <= month <= 12):
        return None
    test_year = year if year else 2024
    try:
        date(test_year, month, day)
        return (day, month, year)
    except ValueError:
        return None


def calculate_next_occurrence(day: int, month: int, from_date: Optional[date] = None) -> Tuple[date, int]:
    today = from_date or get_current_msk_date()
    target_year = today.year

    def get_valid_date(y: int, m: int, d: int) -> date:
        try:
            return date(y, m, d)
        except ValueError:
            if m == 2 and d == 29:
                return date(y, 2, 28)
            raise

    candidate = get_valid_date(target_year, month, day)
    if candidate < today:
        candidate = get_valid_date(target_year + 1, month, day)

    days_left = (candidate - today).days
    return candidate, days_left


def calculate_age(birth_year: Optional[int], target_date: date) -> Optional[int]:
    if not birth_year:
        return None
    return target_date.year - birth_year


def add_birthday(name: str, date_str: str, note: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    parsed = parse_date_string(date_str)
    if not parsed:
        return False, "Неверный формат даты. Примеры: 25.12.1995, 25.12, 5 мая 1990", None

    day, month, year = parsed
    birthdays = load_birthdays()

    for b in birthdays:
        if b["name"].lower() == name.strip().lower() and b["day"] == day and b["month"] == month:
            if note:
                b["note"] = note
            if year:
                b["year"] = year
            save_birthdays(birthdays)
            return True, f"Запись для <b>{b['name']}</b> обновлена!", b

    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "name": name.strip(),
        "day": day,
        "month": month,
        "year": year,
        "note": note.strip(),
        "created_at": datetime.now(MSK_TZ).isoformat()
    }
    birthdays.append(new_entry)
    save_birthdays(birthdays)
    return True, f"✅ Добавлен день рождения: <b>{new_entry['name']}</b> ({format_date_entry(new_entry)})", new_entry


def delete_birthday(identifier: str) -> Tuple[bool, str]:
    birthdays = load_birthdays()
    target_id = identifier.strip().lower()
    
    matched = [b for b in birthdays if b["id"].lower() == target_id]
    if not matched:
        matched = [b for b in birthdays if target_id in b["name"].lower()]

    if not matched:
        return False, f"Запись '{identifier}' не найдена."
    if len(matched) > 1:
        names = ", ".join(f"{b['name']} (ID: {b['id']})" for b in matched)
        return False, f"Найдено несколько: {names}. Укажите точный ID."

    to_remove = matched[0]
    birthdays = [b for b in birthdays if b["id"] != to_remove["id"]]
    save_birthdays(birthdays)
    return True, f"🗑 Запись <b>{to_remove['name']}</b> удалена."


def get_sorted_birthdays(from_date: Optional[date] = None) -> List[Dict[str, Any]]:
    birthdays = load_birthdays()
    today = from_date or get_current_msk_date()

    items_with_meta = []
    for b in birthdays:
        next_dt, days_left = calculate_next_occurrence(b["day"], b["month"], today)
        turning_age = calculate_age(b.get("year"), next_dt)
        items_with_meta.append({
            **b,
            "next_date": next_dt,
            "days_left": days_left,
            "turning_age": turning_age
        })

    items_with_meta.sort(key=lambda x: (x["days_left"], x["name"]))
    return items_with_meta


def format_date_entry(entry: Dict[str, Any]) -> str:
    d = entry["day"]
    m = entry["month"]
    m_name = MONTH_NAMES_RU[m]
    y = entry.get("year")
    if y:
        return f"{d} {m_name} {y} г."
    return f"{d} {m_name}"


def format_age_word(age: int) -> str:
    if 11 <= (age % 100) <= 14:
        return f"{age} лет"
    last = age % 10
    if last == 1:
        return f"{age} год"
    if 2 <= last <= 4:
        return f"{age} года"
    return f"{age} лет"
