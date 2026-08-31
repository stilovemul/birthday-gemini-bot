import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from core.config import DAILY_CHECK_HOUR, DAILY_CHECK_MINUTE, MSK_TZ
from modules.birthdays.notifier import check_and_notify as check_birthdays
from modules.smart_reminders.storage import get_due_reminders, mark_as_done
from modules.drive2_tracker.checker import check_all_drive2_users

logger = logging.getLogger("AppScheduler")


async def check_and_send_smart_reminders(bot: Bot):
    """Checks for due reminders and sends push notifications to users."""
    try:
        due = get_due_reminders()
        for r in due:
            user_id = r["user_id"]
            text = r["text"]
            time_str = datetime.now(MSK_TZ).strftime("%H:%M")
            
            msg = (
                f"⏰🔔 <b>ВНИМАНИЕ: НАПОМИНАНИЕ!</b>\n\n"
                f"📌 <b>{text}</b>\n"
                f"🕒 <i>Время: {time_str} MSK</i>"
            )
            try:
                await bot.send_message(user_id, msg, parse_mode="HTML")
                mark_as_done(r["id"])
                logger.info(f"Reminder sent to {user_id}: '{text}'")
            except Exception as e:
                logger.error(f"Failed to send reminder {r['id']} to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error checking smart reminders: {e}")


async def run_scheduler(bot: Bot):
    """Central scheduler for background jobs (MSK UTC+3)."""
    logger.info("Центральный планировщик запущен (напоминания 20с, Drive2 60с, ДР 09:00 MSK).")
    last_birthday_check_day = None
    drive2_tick = 0

    while True:
        try:
            # 1. Check minute-level smart reminders (every 20s)
            await check_and_send_smart_reminders(bot)

            # 2. Check Drive2 events (every ~60s)
            drive2_tick += 1
            if drive2_tick >= 3:
                drive2_tick = 0
                asyncio.create_task(check_all_drive2_users(bot))

            # 3. Check daily birthdays at 09:00 MSK
            now_msk = datetime.now(MSK_TZ)
            today_str = now_msk.strftime("%Y-%m-%d")

            if now_msk.hour == DAILY_CHECK_HOUR and now_msk.minute <= 5:
                if last_birthday_check_day != today_str:
                    logger.info("Запуск утренней проверки дней рождения в 09:00 MSK...")
                    check_birthdays(force_send=False)
                    last_birthday_check_day = today_str

            await asyncio.sleep(20)
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
            await asyncio.sleep(20)
