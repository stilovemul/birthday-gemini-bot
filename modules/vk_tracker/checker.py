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
    Queries VK API account.getCounters and messages.getConversations (extended=1)
    to accurately retrieve unread dialogs, sender names, text snippets, and counters.
    """
    if not token or not token.strip():
        return False, {"error_code": 5, "error_type": "no_token"}, "VK токен не привязан. Нажмите «🔑 Привязать токен VK»."

    headers = {"User-Agent": "KateMobileAndroid/113.1 lite-548 (Android 14; SDK 34; arm64-v8a; samsung SM-S928B; ru)"}

    try:
        async with aiohttp.ClientSession() as session:
            messages_total = 0
            messages_unmuted = 0
            friends = 0
            notifications = 0
            business_notify = 0
            unread_details = []
            has_any_success = False

            # 1. Fetch counters
            counters_url = f"https://api.vk.com/method/account.getCounters?v={VK_API_VERSION}&access_token={token}"
            try:
                async with session.get(counters_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "response" in data:
                            has_any_success = True
                            counters = data.get("response", {})
                            messages_total = counters.get("messages", 0)
                            messages_unmuted = counters.get("messages_unread_unmuted", 0)
                            friends = counters.get("friends", 0)
                            notifications = max(counters.get("notifications", 0), counters.get("business_notify_all", 0), counters.get("events", 0))
                            business_notify = counters.get("business_notify_all", 0)
                        elif "error" in data:
                            err = data["error"]
                            err_code = err.get("error_code", 0)
                            err_msg = err.get("error_msg", "Ошибка доступа")
                            if err_code in [5, 4, 15, 27, 28]:
                                return False, {"error_code": err_code, "error_type": "auth_failed"}, f"Ошибка авторизации VK ({err_msg}). Требуется обновить токен."
            except Exception as e:
                logger.warning(f"Failed to fetch VK counters: {e}")

            # 2. Fetch friends requests if counters was 0 or not available
            if friends == 0:
                try:
                    friends_url = f"https://api.vk.com/method/friends.getRequests?v={VK_API_VERSION}&access_token={token}&need_viewed=1"
                    async with session.get(friends_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as f_resp:
                        if f_resp.status == 200:
                            f_data = await f_resp.json()
                            if "response" in f_data:
                                has_any_success = True
                                friends = f_data["response"].get("count", 0)
                except Exception:
                    pass

            # 3. Fetch notifications if counters was 0 or not available
            if notifications == 0:
                try:
                    notif_url = f"https://api.vk.com/method/notifications.get?v={VK_API_VERSION}&access_token={token}&count=5"
                    async with session.get(notif_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as n_resp:
                        if n_resp.status == 200:
                            n_data = await n_resp.json()
                            if "response" in n_data:
                                has_any_success = True
                                notifications = n_data["response"].get("count", 0)
                except Exception:
                    pass

            # 4. Fetch conversations details if any unread
            conv_url = f"https://api.vk.com/method/messages.getConversations?filter=unread&extended=1&count=10&v={VK_API_VERSION}&access_token={token}"
            try:
                async with session.get(conv_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as conv_resp:
                    if conv_resp.status == 200:
                        conv_data = await conv_resp.json()
                        if "response" in conv_data:
                            has_any_success = True
                            r = conv_data["response"]
                            conv_count = r.get("count", 0)
                            if conv_count > messages_total:
                                messages_total = conv_count

                            # Build lookups for profiles and groups
                            profiles = {p["id"]: f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() for p in r.get("profiles", [])}
                            groups = {g["id"]: g.get("name", "Сообщество") for g in r.get("groups", [])}

                            items = r.get("items", [])
                            for it in items:
                                conv = it.get("conversation", {})
                                peer = conv.get("peer", {})
                                peer_id = peer.get("id", 0)
                                p_type = peer.get("type", "user")
                                unread_in_conv = conv.get("unread_count", 1)

                                # Determine Title
                                if p_type == "chat":
                                    title = conv.get("chat_settings", {}).get("title", f"Беседа #{peer_id}")
                                elif p_type == "group" or peer_id < 0:
                                    title = groups.get(abs(peer_id), f"Сообщество {peer_id}")
                                else:
                                    title = profiles.get(peer_id, f"Пользователь {peer_id}")

                                # Determine Text / Snippet
                                last_msg = it.get("last_message", {})
                                text = last_msg.get("text", "").replace("\n", " ").strip()

                                # Check attachments
                                attachments = last_msg.get("attachments", [])
                                att_labels = []
                                for att in attachments:
                                    a_type = att.get("type", "")
                                    if a_type == "photo":
                                        att_labels.append("📷 Фото")
                                    elif a_type == "video":
                                        att_labels.append("🎥 Видео")
                                    elif a_type == "audio_message" or a_type == "doc" and att.get("doc", {}).get("type") == 5:
                                        att_labels.append("🎤 Голосовое")
                                    elif a_type == "doc":
                                        att_labels.append("📎 Документ")
                                    elif a_type == "audio":
                                        att_labels.append("🎵 Аудио")
                                    elif a_type == "sticker":
                                        att_labels.append("👾 Стикер")
                                    elif a_type == "gift":
                                        att_labels.append("🎁 Подарок")
                                    elif a_type == "wall":
                                        att_labels.append("📢 Запись")

                                if last_msg.get("fwd_messages"):
                                    att_labels.append("📩 Пересланные сообщ.")

                                if att_labels and not text:
                                    snippet = " | ".join(att_labels)
                                elif att_labels and text:
                                    if len(text) > 40:
                                        text = text[:40] + "..."
                                    snippet = f"{text} ({', '.join(att_labels)})"
                                else:
                                    snippet = text or "[Сообщение]"

                                if len(snippet) > 70:
                                    snippet = snippet[:70] + "..."

                                unread_details.append({
                                    "title": title,
                                    "type": p_type,
                                    "peer_id": peer_id,
                                    "unread_count": unread_in_conv,
                                    "text": snippet
                                })
            except Exception:
                pass

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
        return False, {"error_code": 0, "error_type": "network_error"}, f"Сетевая ошибка VK: {e}"


async def check_vk_for_user(user_id: int, bot: Bot, notify_only_new: bool = True) -> Optional[str]:
    """Checks VK events for a specific user and formats transparent breakdown."""
    config = get_user_vk_config(user_id)
    if not config or not config.get("enabled", True):
        return None

    token = config.get("token", "").strip()
    if not token:
        if not notify_only_new:
            return (
                "🔵 <b>Центр мониторинга ВКонтакте (VK)</b>\n\n"
                "⚪ <i>Токен не привязан. Нажмите «🔑 Привязать токен VK» ниже для настройки.</i>"
            )
        return None

    last_msg = config.get("last_messages", 0)
    last_notif = config.get("last_notifications", 0)
    last_friends = config.get("last_friends", 0)
    vk_name = config.get("user_name", "Олег Уринев")

    success, data, err_info = await fetch_vk_updates(token)
    if not success:
        err_type = data.get("error_type", "error")
        update_vk_state(
            user_id=user_id,
            messages_count=last_msg,
            messages_unmuted_count=config.get("last_messages_unmuted", 0),
            notifications_count=last_notif,
            friends_count=last_friends,
            error=err_type,
            error_msg=err_info
        )
        if not notify_only_new:
            return (
                f"🔵 <b>Центр мониторинга ВКонтакте ({vk_name})</b>\n\n"
                f"⚠️ <b>Статус:</b> <code>{err_info}</code>\n\n"
                "💡 <i>Для возобновления проверки нажмите кнопку «🔑 Обновить токен VK» ниже.</i>"
            )
        return None

    cur_unmuted = data.get("messages_unmuted", 0)
    cur_total = data.get("messages_total", 0)
    cur_notif = data.get("notifications", 0)
    cur_friends = data.get("friends", 0)
    details = data.get("unread_details", [])

    # Total unread dialogs is either total unread or max of counters
    effective_msgs = max(cur_total, cur_unmuted, len(details))

    # Alert condition on new events
    new_messages = max(0, effective_msgs - last_msg) if effective_msgs > last_msg else 0
    new_notifications = max(0, cur_notif - last_notif) if cur_notif > last_notif else 0
    new_friends = max(0, cur_friends - last_friends) if cur_friends > last_friends else 0

    has_new = (new_messages > 0 or new_notifications > 0 or new_friends > 0)

    update_vk_state(
        user_id=user_id,
        messages_count=effective_msgs,
        messages_unmuted_count=cur_unmuted,
        notifications_count=cur_notif,
        friends_count=cur_friends,
        unread_details=details,
        error=None,
        error_msg=None
    )

    if has_new and notify_only_new:
        alert_lines = ["🔵🔔 <b>Новые события ВКонтакте (VK):</b>\n"]
        if new_messages > 0:
            alert_lines.append(f"✉️ Новых входящих диалогов: <b>+{new_messages}</b>")
            for d in details[:3]:
                alert_lines.append(f"   • <b>{d['title']}</b>: <i>«{d['text']}»</i>")
        if new_notifications > 0:
            alert_lines.append(f"🔔 Новых уведомлений / ответов / лайков: <b>+{new_notifications}</b>")
        if new_friends > 0:
            alert_lines.append(f"👥 Новых заявок в друзья: <b>+{new_friends}</b>")

        alert_lines.append("\n👉 <a href='https://vk.com/im'>Открыть ВКонтакте</a>")
        alert_text = "\n".join(alert_lines)

        try:
            await bot.send_message(user_id, alert_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            logger.info(f"VK Push notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send VK push to user {user_id}: {e}")

    # Build clear human-readable status report
    if effective_msgs > 0:
        if cur_unmuted > 0 and cur_unmuted != effective_msgs:
            msg_str = f"<b>{effective_msgs}</b> <i>(личных: {cur_unmuted}, групп/чатов: {effective_msgs - cur_unmuted})</i>"
        else:
            msg_str = f"<b>{effective_msgs}</b>"
    else:
        msg_str = "<b>0</b> <i>(все диалоги прочитаны)</i>"

    detail_lines = []
    if details:
        detail_lines.append("\n📋 <b>Непрочитанные диалоги:</b>")
        for d in details[:5]:
            icon = "👥" if d["type"] == "chat" else ("🤖" if d["type"] == "group" else "👤")
            unread_cnt = f" [+{d['unread_count']}]" if d.get("unread_count", 1) > 1 else ""
            detail_lines.append(f"• {icon} <b>{d['title']}</b>{unread_cnt}: <i>«{d['text']}»</i>")

    status_report = (
        f"🔵 <b>Центр мониторинга ВКонтакте ({vk_name}):</b>\n\n"
        f"✉️ Непрочитанных диалогов: {msg_str}\n"
        f"🔔 Уведомлений / событий: <b>{cur_notif}</b>\n"
        f"👥 Заявок в друзья: <b>{cur_friends}</b>\n"
        + "\n".join(detail_lines) + "\n\n"
        + ("✨ <i>Все входящие сообщения прочитаны!</i>" if effective_msgs == 0 else "⚡ <i>Есть непрочитанные сообщения в VK!</i>")
        + "\n\n🔗 <a href='https://vk.com/im'>Открыть диалоги VK</a>"
    )
    return status_report


async def check_all_vk_users(bot: Bot) -> None:
    """Iterates through all users in background every 60s with error cooldown."""
    configs = load_vk_configs()
    for uid_str, cfg in configs.items():
        if cfg.get("enabled", True) and cfg.get("token"):
            # Check if recently hit flood control / auth error to avoid continuous hammer
            last_err = cfg.get("last_error")
            if last_err in ["flood_control", "auth_failed"]:
                # Log only periodically, do not hammer VK API every 60s
                continue
            try:
                await check_vk_for_user(int(uid_str), bot, notify_only_new=True)
            except Exception as e:
                logger.warning(f"Error checking VK for user {uid_str}: {e}")
            await asyncio.sleep(1.5)

