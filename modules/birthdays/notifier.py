import json
import logging
import urllib.request
import urllib.parse
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID, SENT_HISTORY_FILE, REMIND_DAYS_BEFORE, MSK_TZ
from modules.birthdays.storage import get_sorted_birthdays, format_date_entry, format_age_word, get_current_msk_date

logger = logging.getLogger("BirthdayNotifier")


def send_telegram_message(text: str, chat_id: Optional[int] = None, parse_mode: str = "HTML") -> bool:
    target_chat = chat_id or TELEGRAM_USER_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat:
        logger.error("Telegram Bot Token or User ID is missing.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                logger.info(f"Notification sent successfully to {target_chat}")
                return True
            else:
                logger.error(f"Telegram API Error: {res_data}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def load_sent_history() -> Dict[str, str]:
    if not SENT_HISTORY_FILE.exists():
        return {}
    try:
        with open(SENT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_sent_history(history: Dict[str, str]) -> None:
    today = get_current_msk_date()
    cleaned = {}
    for k, v in history.items():
        try:
            record_date_str = k.split("_")[0]
            rec_dt = datetime.strptime(record_date_str, "%Y-%m-%d").date()
            if (today - rec_dt).days <= 30:
                cleaned[k] = v
        except Exception:
            pass

    SENT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)


def format_birthday_notification(item: Dict[str, Any], days_left: int) -> str:
    name = item["name"]
    next_date = item["next_date"]
    date_formatted = next_date.strftime("%d.%m")
    turning_age = item.get("turning_age")
    note = item.get("note", "").strip()

    age_text = ""
    if turning_age:
        age_word = format_age_word(turning_age)
        if days_left == 0:
            age_text = f" (исполняется <b>{age_word}</b>! 🎉)"
        else:
            age_text = f" (исполнится <b>{age_word}</b>)"

    note_text = f"\n🎁 <i>Заметка: {note}</i>" if note else ""

    if days_left == 0:
        return (
            f"🎂🎉 <b>СЕГОДНЯ ДЕНЬ РОЖДЕНИЯ!</b> 🎉🎂\n\n"
            f"👤 <b>{name}</b>{age_text}\n"
            f"🗓 <b>{format_date_entry(item)}</b>"
            f"{note_text}\n\n"
            f"✨ <i>Не забудьте поздравить!</i> 🥳"
        )
    elif days_left == 1:
        return (
            f"⏳ <b>Напоминание: ЗАВТРА день рождения!</b>\n\n"
            f"👤 <b>{name}</b>{age_text}\n"
            f"🗓 Завтра ({date_formatted})"
            f"{note_text}\n\n"
            f"💡 <i>Самое время подготовить поздравление или подарок!</i>"
        )
    elif days_left in (2, 3, 4):
        return (
            f"⏳ <b>Напоминание: через {days_left} дня день рождения!</b>\n\n"
            f"👤 <b>{name}</b>{age_text}\n"
            f"🗓 Дата: <b>{date_formatted}</b>"
            f"{note_text}\n\n"
            f"🎁 <i>Осталось немного времени на подготовку подарка.</i>"
        )
    else:
        return (
            f"🗓 <b>Напоминание: через {days_left} дней день рождения!</b>\n\n"
            f"👤 <b>{name}</b>{age_text}\n"
            f"🗓 Дата: <b>{date_formatted}</b>"
            f"{note_text}\n\n"
            f"💡 <i>Запланируйте покупку подарка заранее!</i>"
        )


def check_and_notify(force_send: bool = False, chat_id: Optional[int] = None) -> List[str]:
    today = get_current_msk_date()
    today_str = today.strftime("%Y-%m-%d")
    history = load_sent_history()
    birthdays = get_sorted_birthdays(today)
    
    sent_list = []

    for item in birthdays:
        days_left = item["days_left"]

        if days_left in REMIND_DAYS_BEFORE:
            history_key = f"{today_str}_{item['id']}_{days_left}"

            if not force_send and history_key in history:
                logger.info(f"Already sent today for {item['name']} (days_left={days_left})")
                continue

            msg = format_birthday_notification(item, days_left)
            success = send_telegram_message(msg, chat_id=chat_id)
            if success:
                history[history_key] = datetime.now(MSK_TZ).isoformat()
                sent_list.append(f"{item['name']} (через {days_left} дн.)")

    save_sent_history(history)
    return sent_list
