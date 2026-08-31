import logging
from datetime import datetime
from aiogram import Bot
from core.config import MSK_TZ
from modules.custom_rules.storage import _load_raw, _save_raw

logger = logging.getLogger("CustomRulesEngine")


async def evaluate_and_run_custom_rules(bot: Bot):
    """
    Evaluates all active custom rules against current MSK time and executes corresponding actions.
    """
    try:
        now_msk = datetime.now(MSK_TZ)
        today_date_str = now_msk.strftime("%Y-%m-%d")
        current_time_slot = now_msk.strftime("%Y-%m-%d %H:%M")
        curr_hour = now_msk.hour
        curr_min = now_msk.minute
        curr_dom = now_msk.day
        curr_dow = now_msk.weekday()  # 0=Monday, 6=Sunday

        rules = _load_raw()
        changed = False

        for r in rules:
            if not r.get("is_active", True):
                continue

            last_trig = r.get("last_triggered", "")
            # Prevent multiple triggers within the same day for daily/weekly/monthly rules
            if last_trig.startswith(today_date_str):
                continue

            trig_type = r.get("trigger_type", "daily_time")
            r_hour = r.get("hour", 12)
            r_min = r.get("minute", 0)

            # Match hour and minute (with 5 min window allowance)
            if curr_hour != r_hour or abs(curr_min - r_min) > 4:
                continue

            should_fire = False

            if trig_type == "daily_time":
                should_fire = True
            elif trig_type == "monthly_day":
                target_dom = r.get("day_of_month", 1)
                if curr_dom == target_dom:
                    should_fire = True
            elif trig_type == "weekly_day":
                target_dows = r.get("days_of_week", [])
                if curr_dow in target_dows:
                    should_fire = True

            if should_fire:
                user_id = r.get("user_id", 157236577)
                title = r.get("title", "Персональное правило")
                act_text = r.get("action_text", "")

                msg = (
                    f"🧩⚡ <b>ПЕРСОНАЛЬНОЕ ПРАВИЛО СРАБОТАЛО:</b>\n\n"
                    f"📌 <b>{title}</b>\n\n"
                    f"👉 {act_text}\n\n"
                    f"🕒 <i>Время: {now_msk.strftime('%d.%m.%Y в %H:%M MSK')}</i>"
                )

                try:
                    await bot.send_message(user_id, msg, parse_mode="HTML")
                    r["last_triggered"] = current_time_slot
                    changed = True
                    logger.info(f"Custom rule fired for {user_id}: '{title}'")
                except Exception as e:
                    logger.error(f"Failed to execute rule {r.get('id')}: {e}")

        if changed:
            _save_raw(rules)
    except Exception as e:
        logger.error(f"Error in custom rules engine: {e}")
