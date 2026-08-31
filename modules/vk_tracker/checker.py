import aiohttp
import asyncio
import logging
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
from aiogram import Bot
from aiogram.enums import ParseMode

from modules.vk_tracker.storage import (
    load_vk_configs,
    get_user_vk_config,
    update_vk_state
)

logger = logging.getLogger("VKChecker")
VK_API_VERSION = "5.199"


async def fetch_vk_updates(token: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    Queries VK API account.getCounters and notifications.get using user's access token.
    """
    if not token:
        return False, {}, "VK токен не указан. Отправьте /vk_token [ВАШ_ТОКЕН]"

    url = f"https://api.vk.com/method/account.getCounters?v={VK_API_VERSION}&access_token={token}"
    headers = {"User-Agent": "VKAndroidApp/8.55 (Android 14; ru; 1080x2400)"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return False, {}, f"Ошибка VK API: HTTP {resp.status}"

                data = await resp.json()
                if "error" in data:
                    err_msg = data["error"].get("error_msg", "Неверный токен или ошибка доступа")
                    return False, {}, f"Ошибка VK: {err_msg}"

                counters = data.get("response", {})
                messages = counters.get("messages", 0)
                friends = counters.get("friends", 0)
                notifications = counters.get("notifications", 0)
                app_requests = counters.get("app_requests", 0)

                return True, {
                    "messages": messages,
                    "friends": friends,
                    "notifications": notifications,
                    "app_requests": app_requests,
                    "raw": counters
                }, "OK"

    except Exception as e:
        logger.error(f"VK fetch error: {e}")
        return False, {}, f"Сетевая ошибка VK: {e}"


async def check_vk_for_user(user_id: int, bot: Bot, notify_only_new: bool = True) -> Optional[str]:
    """Checks VK events for a specific user and sends alert if new events arrived."""
    config = get_user_vk_config(user_id)
    if not config or not config.get("enabled", True):
        return None

    token = config.get("token", "").strip()
    if not token:
        return None

    last_msg = config.get("last_messages", 0)
    last_notif = config.get("last_notifications", 0)
    last_friends = config.get("last_friends", 0)

    success, data, err_info = await fetch_vk_updates(token)
    if not success:
        logger.warning(f"VK check failed for user {user_id}: {err_info}")
        return None

    cur_msg = data.get("messages", 0)
    cur_notif = data.get("notifications", 0)
    cur_friends = data.get("friends", 0)

    # Detect new events
    new_messages = max(0, cur_msg - last_msg) if cur_msg > last_msg else 0
    new_notifications = max(0, cur_notif - last_notif) if cur_notif > last_notif else 0
    new_friends = max(0, cur_friends - last_friends) if cur_friends > last_friends else 0

    has_new = (new_messages > 0 or new_notifications > 0 or new_friends > 0)

    update_vk_state(
        user_id=user_id,
        messages_count=cur_msg,
        notifications_count=cur_notif,
        friends_count=cur_friends
    )

    if has_new and notify_only_new:
        alert_lines = ["🔵🔔 <b>Новые события ВКонтакте (VK):</b>\n"]
        if new_messages > 0:
            alert_lines.append(f"✉️ Новых сообщений в диалогах: <b>+{new_messages}</b> (всего непрочитанных: {cur_msg})")
        if new_notifications > 0:
            alert_lines.append(f"🔔 Новых уведомлений / ответов / лайков: <b>+{new_notifications}</b>")
        if new_friends > 0:
            alert_lines.append(f"👥 Новых заявок в друзья: <b>+{new_friends}</b>")

        alert_lines.append("\n👉 <i>Откройте VK, чтобы прочитать сообщения.</i>")
        alert_text = "\n".join(alert_lines)

        try:
            await bot.send_message(user_id, alert_text, parse_mode=ParseMode.HTML)
            logger.info(f"VK Push notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send VK push to user {user_id}: {e}")

    # Return manual check status text
    status_report = (
        f"🔵 <b>Статус ВКонтакте (VK):</b>\n\n"
        f"✉️ Непрочитанных сообщений: <b>{cur_msg}</b>\n"
        f"🔔 Новых уведомлений / реакций: <b>{cur_notif}</b>\n"
        f"👥 Заявок в друзья: <b>{cur_friends}</b>\n\n"
        + ("✨ <i>Все входящие сообщения прочитаны!</i>" if (cur_msg == 0 and cur_notif == 0 and cur_friends == 0) else "⚡ <i>Есть непрочитанные события!</i>")
    )
    return status_report


async def check_all_vk_users(bot: Bot) -> None:
    """Iterates through all users in background every 60s."""
    configs = load_vk_configs()
    for uid_str, cfg in configs.items():
        if cfg.get("enabled", True) and cfg.get("token"):
            try:
                await check_vk_for_user(int(uid_str), bot, notify_only_new=True)
            except Exception as e:
                logger.warning(f"Error checking VK for user {uid_str}: {e}")
            await asyncio.sleep(1.5)
