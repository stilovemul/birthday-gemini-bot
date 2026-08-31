import logging
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.config import MSK_TZ
from modules.custom_rules.storage import (
    _load_raw,
    _save_raw,
    is_rule_completed_for_current_period,
    is_rule_in_active_window,
    get_current_period_key
)

logger = logging.getLogger("CustomRulesEngine")


async def evaluate_and_run_custom_rules(bot: Bot):
    """
    Evaluates all active custom rules.
    If a rule is within its active window (e.g. 20-24 of the month) AND NOT yet completed (green badge),
    it sends an alert with a one-click completion button.
    """
    try:
        now_msk = datetime.now(MSK_TZ)
        today_date_str = now_msk.strftime("%Y-%m-%d")
        curr_hour = now_msk.hour
        curr_min = now_msk.minute

        rules = _load_raw()
        changed = False

        for r in rules:
            if not r.get("is_active", True):
                continue

            # Check if user already marked this rule as done for this period (e.g. this month)
            if is_rule_completed_for_current_period(r):
                continue

            # Check if today is in the active trigger window
            if not is_rule_in_active_window(r):
                continue

            # Match hour and minute (e.g. 12:00 MSK, ±4 mins)
            r_hour = r.get("hour", 12)
            r_min = r.get("minute", 0)
            if curr_hour != r_hour or abs(curr_min - r_min) > 4:
                continue

            # Ensure we only send once per day during the window
            last_notif = r.get("last_notified_date", "")
            if last_notif == today_date_str:
                continue

            user_id = r.get("user_id", 157236577)
            title = r.get("title", "Персональное правило")
            act_text = r.get("action_text", "")
            rule_id = r.get("id")

            # Notification message with fast completion button
            tt = r.get("trigger_type", "")
            if tt == "monthly_range":
                window_desc = f"Период: {r.get('start_day')}–{r.get('end_day')} числа"
            elif tt == "monthly_day":
                window_desc = f"Число месяца: {r.get('day_of_month')}-е"
            else:
                window_desc = "Ежедневная задача"

            msg = (
                f"🧩🔔 <b>ПЕРСОНАЛЬНОЕ НАПОМИНАНИЕ:</b>\n\n"
                f"📌 <b>{title}</b>\n"
                f"🗓 <i>{window_desc}</i>\n\n"
                f"👉 <b>{act_text}</b>\n\n"
                f"💡 <i>Нажмите кнопку ниже, чтобы подтвердить выполнение и отключить напоминания на этот период.</i>"
            )

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Отметить выполненным!",
                            callback_data=f"rule_done_{rule_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🧩 Открыть Мои правила",
                            callback_data="rule_refresh"
                        )
                    ]
                ]
            )

            try:
                await bot.send_message(user_id, msg, parse_mode="HTML", reply_markup=kb)
                r["last_notified_date"] = today_date_str
                changed = True
                logger.info(f"Persistent rule notification sent to {user_id}: '{title}'")
            except Exception as e:
                logger.error(f"Failed to send rule notification {rule_id}: {e}")

        if changed:
            _save_raw(rules, sync_cloud=False)
    except Exception as e:
        logger.error(f"Error in custom rules engine: {e}")
