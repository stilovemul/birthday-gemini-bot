import asyncio
import logging
from datetime import datetime, timedelta
from core.config import DAILY_CHECK_HOUR, DAILY_CHECK_MINUTE, MSK_TZ
from modules.birthdays.notifier import check_and_notify

logger = logging.getLogger("AppScheduler")


async def run_scheduler():
    """Central scheduler for background jobs (runs in MSK timezone)."""
    logger.info("Центральный планировщик запущен (MSK UTC+3).")
    while True:
        try:
            now = datetime.now(MSK_TZ)
            target = now.replace(hour=DAILY_CHECK_HOUR, minute=DAILY_CHECK_MINUTE, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            sleep_seconds = (target - now).total_seconds()
            logger.info(f"Следующая плановая проверка ДР в {target.strftime('%Y-%m-%d %H:%M MSK')}")
            
            await asyncio.sleep(min(sleep_seconds, 3600))
            
            current = datetime.now(MSK_TZ)
            if current.hour == DAILY_CHECK_HOUR and current.minute <= 5:
                logger.info("Запуск проверки дней рождения по расписанию...")
                check_and_notify(force_send=False)
                await asyncio.sleep(600)
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(60)
