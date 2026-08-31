import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from core.config import DAILY_CHECK_HOUR, DAILY_CHECK_MINUTE, MSK_TZ
from modules.birthdays.notifier import check_and_notify as check_birthdays
from modules.smart_reminders.storage import get_due_reminders, mark_as_done
from modules.drive2_tracker.checker import check_all_drive2_users
from modules.vk_tracker.checker import check_all_vk_users
from modules.max_tracker.checker import check_all_max_users
from modules.weather_synoptic.service import check_all_weather_alerts
from modules.morning_digest.digest import send_morning_digest_to_user
from modules.subscription_tracker.checker import check_all_subscription_notifications
from modules.custom_rules.engine import evaluate_and_run_custom_rules

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
    logger.info("Центральный планировщик запущен (напоминания 20с, Drive2 60с, VK 60с, MAX 60с, Погода 10мин, Дайджест 09:00 MSK).")
    last_daily_check_day = None
    tick_60s = 0
    weather_tick = 0

    while True:
        try:
            # 1. Check minute-level smart reminders & custom rules (every 20s)
            await check_and_send_smart_reminders(bot)
            await evaluate_and_run_custom_rules(bot)

            # 2. Check Drive2, VK, MAX events & subscriptions (every ~60s = 3 ticks of 20s)
            tick_60s += 1
            if tick_60s >= 3:
                tick_60s = 0
                asyncio.create_task(check_all_drive2_users(bot))
                asyncio.create_task(check_all_vk_users(bot))
                asyncio.create_task(check_all_max_users(bot))
                asyncio.create_task(check_all_subscription_notifications(bot))

            # 3. Check impending precipitation radar (every ~10 mins = 30 ticks of 20s)
            weather_tick += 1
            if weather_tick >= 30:
                weather_tick = 0
                asyncio.create_task(check_all_weather_alerts(bot))

            # 4. Morning Digest & Birthday alerts at 09:00 MSK
            now_msk = datetime.now(MSK_TZ)
            today_str = now_msk.strftime("%Y-%m-%d")

            if now_msk.hour == DAILY_CHECK_HOUR and now_msk.minute <= 5:
                if last_daily_check_day != today_str:
                    logger.info("Запуск персонального утреннего дайджеста в 09:00 MSK...")
                    # Send rich morning digest
                    asyncio.create_task(send_morning_digest_to_user(157236577, bot))
                    # Also notify if any exact birthday is today
                    check_birthdays(force_send=False)
                    last_daily_check_day = today_str

            await asyncio.sleep(20)
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
            await asyncio.sleep(20)
