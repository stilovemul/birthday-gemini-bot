import aiohttp
import asyncio
import logging
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
    Queries VK API account.getCounters and messages.getConversations to accurately distinguish
    important personal unread messages from muted group/bot spam.
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
                messages_total = counters.get("messages", 0)
                messages_unmuted = counters.get("messages_unread_unmuted", 0)
                friends = counters.get("friends", 0)
                notifications = counters.get("notifications", 0)
                business_notify = counters.get("business_notify_all", 0)

                # Fetch detailed unread items list
                unread_details = []
                if messages_total > 0:
                    conv_url = f"https://api.vk.com/method/messages.getConversations?filter=unread&count=5&v={VK_API_VERSION}&access_token={token}"
                    async with session.get(conv_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as conv_resp:
                        if conv_resp.status == 200:
                            conv_data = await conv_resp.json()
                            items = conv_data.get("response", {}).get("items", [])
                            for it in items:
                                last_msg = it.get("last_message", {})
                                peer = it.get("conversation", {}).get("peer", {})
                                p_type = peer.get("type", "user")
                                text_snippet = last_msg.get("text", "").replace("\n", " ").strip()
                                if len(text_snippet) > 60:
                                    text_snippet = text_snippet[:60] + "..."
                                unread_details.append({
                                    "type": p_type,
                                    "text": text_snippet or "[Вложение / Действие]"
                                })

                return True, {
                    "messages_total": messages_total,
                    "messages_unmuted": messages_unmuted,
                    "friends": friends,
                    "notifications": notifications,
                    "business_notify": business_notify,
                    "unread_details": unread_details
                }, "OK"

    except Exception as e:
        logger.error(f"VK fetch error: {e}")
        return False, {}, f"Сетевая ошибка VK: {e}"


async def check_vk_for_user(user_id: int, bot: Bot, notify_only_new: bool = True) -> Optional[str]:
    """Checks VK events for a specific user and formats transparent breakdown."""
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

    cur_unmuted = data.get("messages_unmuted", 0)
    cur_total = data.get("messages_total", 0)
    cur_notif = data.get("notifications", 0)
    cur_friends = data.get("friends", 0)
    details = data.get("unread_details", [])

    # We alert on important unmuted messages or new friend requests / notifications
    new_unmuted = max(0, cur_unmuted - last_msg) if cur_unmuted > last_msg else 0
    new_notifications = max(0, cur_notif - last_notif) if cur_notif > last_notif else 0
    new_friends = max(0, cur_friends - last_friends) if cur_friends > last_friends else 0

    has_new = (new_unmuted > 0 or new_notifications > 0 or new_friends > 0)

    update_vk_state(
        user_id=user_id,
        messages_count=cur_unmuted,
        notifications_count=cur_notif,
        friends_count=cur_friends
    )

    if has_new and notify_only_new:
        alert_lines = ["🔵🔔 <b>Новые события ВКонтакте (VK):</b>\n"]
        if new_unmuted > 0:
            alert_lines.append(f"✉️ Новых личных сообщений от пользователей: <b>+{new_unmuted}</b>")
        if new_notifications > 0:
            alert_lines.append(f"🔔 Новых уведомлений / ответов / лайков: <b>+{new_notifications}</b>")
        if new_friends > 0:
            alert_lines.append(f"👥 Новых заявок в друзья: <b>+{new_friends}</b>")

        alert_lines.append("\n👉 <i>Откройте VK, чтобы прочитать.</i>")
        alert_text = "\n".join(alert_lines)

        try:
            await bot.send_message(user_id, alert_text, parse_mode=ParseMode.HTML)
            logger.info(f"VK Push notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send VK push to user {user_id}: {e}")

    # Build clear human-readable status report
    if cur_unmuted > 0:
        msg_str = f"<b>{cur_unmuted}</b> <i>(новые личные сообщения)</i>"
    elif cur_total > 0:
        msg_str = f"<b>0</b> от людей <i>(1 в заглушенных ботах/сообществах)</i>"
    else:
        msg_str = "<b>0</b> <i>(все диалоги прочитаны)</i>"

    detail_lines = []
    if details:
        detail_lines.append("\n📋 <b>Непрочитанное:</b>")
        for d in details:
            prefix = "🤖 Бот/Группа" if d["type"] == "group" else "👤 Диалог"
            detail_lines.append(f"• {prefix}: <i>«{d['text']}»</i>")

    status_report = (
        f"🔵 <b>Центр мониторинга ВКонтакте (VK):</b>\n\n"
        f"✉️ Личных сообщений: {msg_str}\n"
        f"🔔 Новых уведомлений: <b>{cur_notif}</b>\n"
        f"👥 Заявок в друзья: <b>{cur_friends}</b>\n"
        + "\n".join(detail_lines) + "\n\n"
        + ("✨ <i>Важных непрочитанных сообщений нет!</i>" if cur_unmuted == 0 else "⚡ <i>Есть новые входящие от пользователей!</i>")
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
