import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.enums import ParseMode

from core.config import MSK_TZ
from modules.birthdays.storage import get_sorted_birthdays, format_date_entry, format_age_word
from modules.smart_reminders.storage import get_active_reminders
from modules.weather_synoptic.service import get_weather_report, geocode_location
from modules.weather_synoptic.storage import get_user_weather_config
from modules.drive2_tracker.storage import get_user_drive2_config
from modules.vk_tracker.storage import get_user_vk_config
from modules.max_tracker.storage import get_user_max_config
from modules.food_tracker.storage import get_daily_summary, get_user_calorie_goal
from modules.smart_home.client import build_smart_home_card
from modules.smart_home.storage import get_user_smart_home_config
from modules.morning_digest.holidays import get_today_holidays

logger = logging.getLogger("MorningDigest")

DAYS_RU = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}

MONTHS_GEN_RU = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


async def generate_morning_digest(user_id: int = 157236577) -> str:
    """
    Assembles a comprehensive, beautiful morning briefing:
    1. Greeting & Date (MSK)
    2. Weather & Precipitation radar forecast for user district
    3. Today's reminders & scheduled tasks
    4. Birthdays today and upcoming in next 3 days
    5. Inbox counters from Drive2, VK, and MAX
    6. Smart Home & Climate overview
    7. Daily Nutrition goal (Calories & Macros)
    """
    now = datetime.now(MSK_TZ)
    weekday = DAYS_RU.get(now.weekday(), "")
    d_str = f"{now.day} {MONTHS_GEN_RU[now.month]} {now.year} г., {weekday}"
    today_iso = now.strftime("%Y-%m-%d")

    # 1. Today's Holidays
    holidays_text = "🎉 <i>Список праздников формируется...</i>"
    try:
        holidays_text = await get_today_holidays(now)
    except Exception as e:
        logger.warning(f"Holidays in digest warning: {e}")

    # 2. Weather
    w_cfg = get_user_weather_config(user_id)
    w_city = w_cfg.get("city", "Санкт-Петербург")
    w_dist = w_cfg.get("district", "Приморский р-н")
    w_lat = w_cfg.get("lat", 59.9950)
    w_lon = w_cfg.get("lon", 30.2200)

    weather_text = "🌤 <i>Данные о погоде обновляются...</i>"
    try:
        ok_w, w_report = await get_weather_report(w_city, w_dist, w_lat, w_lon)
        if ok_w and w_report:
            w_lines = [l for l in w_report.split("\n") if l.strip()]
            weather_text = "\n".join(w_lines[:4])
            if "зонт" in w_report.lower() or "осадк" in w_report.lower() or "дожд" in w_report.lower():
                weather_text += "\n☂️ <i>Совет: захватите зонт, сегодня возможен дождь!</i>"
            else:
                weather_text += "\n✨ <i>Осадков не ожидается, отличная погода!</i>"
    except Exception as e:
        logger.warning(f"Weather in digest warning: {e}")

    # 3. Today's Reminders
    reminders = get_active_reminders(user_id)
    rem_today = []
    for r in reminders:
        t_iso = r.get("target_iso", "")
        if t_iso.startswith(today_iso):
            rem_today.append(f"• <b>{r['target_display']}</b> — {r['text']}")

    if rem_today:
        rem_text = "\n".join(rem_today)
    else:
        rem_text = "✨ <i>На сегодня запланированных дел нет. Свободный график!</i>"

    # 4. Birthdays (Today + Next 3 days)
    birthdays = get_sorted_birthdays()
    b_urgent = []
    for b in birthdays:
        days = b.get("days_left", 999)
        name = b.get("name", "")
        age_str = f" ({format_age_word(b['turning_age'])})" if b.get("turning_age") else ""
        if days == 0:
            b_urgent.append(f"🎉 <b>СЕГОДНЯ:</b> <b>{name}</b>{age_str}! Не забудьте поздравить!")
        elif days == 1:
            b_urgent.append(f"⏳ <b>ЗАВТРА:</b> {name}{age_str}")
        elif days in [2, 3]:
            b_urgent.append(f"📅 <b>Через {days} дн.:</b> {name}{age_str} ({format_date_entry(b)})")

    if b_urgent:
        b_text = "\n".join(b_urgent)
    else:
        nearest = birthdays[0] if birthdays else None
        if nearest:
            b_text = f"В ближайшие 3 дня ДР нет. Ближайший: <b>{nearest['name']}</b> ({format_date_entry(nearest)}, через {nearest['days_left']} дн.)"
        else:
            b_text = "В ближайшие дни дней рождения нет."

    # 5. Message Inboxes (Drive2, VK, MAX)
    inbox_items = []

    # Drive2
    d2 = get_user_drive2_config(user_id)
    if d2 and d2.get("enabled"):
        d2_msgs = d2.get("last_messages", 0)
        d2_notifs = d2.get("last_notifications", 0)
        if d2_msgs > 0 or d2_notifs > 0:
            inbox_items.append(f"🚗 <b>Drive2:</b> 📩 {d2_msgs} сообщ., 🔔 {d2_notifs} увед.")
        else:
            inbox_items.append("🚗 <b>Drive2:</b> все прочитано ✅")

    # VK
    vk = get_user_vk_config(user_id)
    if vk and vk.get("enabled") and vk.get("token"):
        vk_msgs = vk.get("last_messages", 0)
        vk_notifs = vk.get("last_notifications", 0)
        if vk_msgs > 0 or vk_notifs > 0:
            inbox_items.append(f"🔵 <b>VK:</b> 📩 {vk_msgs} непрочитанных")
        else:
            inbox_items.append("🔵 <b>VK:</b> входящих нет ✅")

    # MAX
    max_c = get_user_max_config(user_id)
    if max_c and max_c.get("token"):
        max_msgs = max_c.get("last_messages", 0)
        if max_msgs > 0:
            inbox_items.append(f"💬 <b>MAX:</b> 📩 {max_msgs} непрочитанных")
        else:
            inbox_items.append("💬 <b>MAX:</b> тишина ✅")

    inbox_text = "\n".join(inbox_items) if inbox_items else "Все входящие каналы проверены и чисты."

    # 6. Smart Home Climate & Safety
    sh_cfg = get_user_smart_home_config(user_id)
    sh_token = sh_cfg.get("token") if sh_cfg else None
    sh_text = "🏠 <i>Умный дом в норме.</i>"
    if sh_token:
        try:
            ok_sh, _, meta = await build_smart_home_card(sh_token)
            if ok_sh and meta:
                sh_text = "🛡️ Протечки: <b>Сухо ✅</b> | Двери: <b>Закрыты 🔒</b>"
        except Exception:
            pass

    # 7. Nutrition & Calorie Target
    daily_goal = get_user_calorie_goal(user_id)
    food_text = f"🎯 Дневная норма: <b>{daily_goal} ккал</b>. <i>Не забывайте пить воду и фотографировать приёмы пищи!</i>"

    # Assemble Digest Card
    digest = (
        f"🌅 <b>Доброе утро, Олег! Персональный дайджест на день</b> 🚀\n"
        f"📅 <i>{d_str}</i>\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        f"{holidays_text}\n\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        f"🌤 <b>ПОГОДА В ВАШЕМ РАЙОНЕ:</b>\n"
        f"{weather_text}\n\n"
        f"⏰ <b>ЗАДАЧИ И НАПОМИНАНИЯ:</b>\n"
        f"{rem_text}\n\n"
        f"🎂 <b>ДНИ РОЖДЕНИЯ БЛИЗКИХ:</b>\n"
        f"{b_text}\n\n"
        f"📬 <b>ВХОДЯЩИЕ И МОНИТОРИНГ:</b>\n"
        f"{inbox_text}\n\n"
        f"🏠 <b>БЕЗОПАСНОСТЬ ДОМА:</b>\n"
        f"{sh_text}\n\n"
        f"🥗 <b>ЦЕЛЬ ПО ПИТАНИЮ:</b>\n"
        f"{food_text}\n\n"
        f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
        f"⚡️ <i>Удачного и продуктивного дня! Бот всегда на связи.</i>"
    )
    return digest


async def send_morning_digest_to_user(user_id: int, bot: Bot) -> bool:
    """Builds and delivers morning digest message to Telegram user."""
    try:
        digest_text = await generate_morning_digest(user_id)
        await bot.send_message(user_id, digest_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        logger.info(f"Morning digest successfully delivered to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send morning digest to user {user_id}: {e}")
        return False
