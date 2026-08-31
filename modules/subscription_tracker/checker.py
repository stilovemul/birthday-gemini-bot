import logging
from datetime import datetime
from aiogram import Bot
from core.config import MSK_TZ
from modules.subscription_tracker.storage import _load_raw, _save_raw

logger = logging.getLogger("SubscriptionChecker")


async def check_all_subscription_notifications(bot: Bot):
    """
    Checks upcoming subscription payments (2 days before, 1 day before, today)
    and sends a push reminder to prevent unexpected card charges.
    """
    try:
        today = datetime.now(MSK_TZ).date()
        today_str = today.strftime("%Y-%m-%d")
        subs = _load_raw()
        changed = False

        for s in subs:
            np_str = s.get("next_payment_date", "")
            if not np_str:
                continue

            try:
                np_date = datetime.strptime(np_str, "%Y-%m-%d").date()
                days_left = (np_date - today).days

                # Notify if 2 days left, 1 day left, or today, and not yet notified today
                if 0 <= days_left <= 2:
                    last_notif = s.get("last_notified", "")
                    if last_notif != today_str:
                        user_id = s.get("user_id", 157236577)
                        name = s.get("name", "Подписка")
                        amount = s.get("amount", 0)
                        card = s.get("card_comment", "Карта")
                        cat = s.get("category", "Сервисы")

                        if days_left == 0:
                            when_str = "<b>СЕГОДНЯ!</b>"
                        elif days_left == 1:
                            when_str = "<b>ЗАВТРА</b>"
                        else:
                            when_str = "<b>через 2 дня</b>"

                        msg = (
                            f"💳🔔 <b>НАПОМИНАНИЕ О СПИСАНИИ ПО ПОДПИСКЕ:</b>\n\n"
                            f"• Сервис: <b>{name}</b> ({cat})\n"
                            f"• Сумма к списанию: <b>{amount} ₽</b>\n"
                            f"• Списание: {when_str} (<i>{np_date.strftime('%d.%m.%Y')}</i>)\n"
                            f"• Привязано к: <i>{card}</i>\n\n"
                            f"💡 <i>Проверьте баланс на карте или отмените подписку, если она больше не нужна.</i>"
                        )
                        try:
                            await bot.send_message(user_id, msg, parse_mode="HTML")
                            s["last_notified"] = today_str
                            changed = True
                            logger.info(f"Subscription alert sent to {user_id} for '{name}'")
                        except Exception as e:
                            logger.error(f"Failed to send sub alert to {user_id}: {e}")
            except Exception as e:
                logger.error(f"Error parsing sub date: {e}")

        if changed:
            _save_raw(subs)
    except Exception as e:
        logger.error(f"Error in subscription checker: {e}")
