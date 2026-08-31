import aiohttp
import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from aiogram import Bot
from aiogram.enums import ParseMode

from modules.drive2_tracker.storage import (
    load_drive2_configs,
    update_drive2_state,
    get_user_drive2_config
)

logger = logging.getLogger("Drive2Checker")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}


async def parse_drive2_counters(html: str) -> Tuple[int, int]:
    """Extracts unread messages count and unread notifications count from Drive2 HTML."""
    messages = 0
    notifications = 0

    # 1. Unread messages counter regex
    msg_match = re.search(r'href=["\']/my/messages/["\'][^>]*>.*?<span[^>]*class=["\'][^"\']*badge[^"\']*["\'][^>]*>([0-9]+)</span>', html, re.DOTALL | re.IGNORECASE)
    if not msg_match:
        msg_match = re.search(r'data-counter=["\']messages["\'][^>]*>([0-9]+)<', html, re.IGNORECASE)
    if msg_match:
        try:
            messages = int(msg_match.group(1).strip())
        except Exception:
            pass

    # 2. Unread notifications counter regex
    notif_match = re.search(r'href=["\']/my/notifications/["\'][^>]*>.*?<span[^>]*class=["\'][^"\']*badge[^"\']*["\'][^>]*>([0-9]+)</span>', html, re.DOTALL | re.IGNORECASE)
    if not notif_match:
        notif_match = re.search(r'data-counter=["\']notifications["\'][^>]*>([0-9]+)<', html, re.IGNORECASE)
    if notif_match:
        try:
            notifications = int(notif_match.group(1).strip())
        except Exception:
            pass

    return messages, notifications


async def parse_recent_notification_items(html: str) -> List[Dict[str, str]]:
    """Extracts recent notification titles / authors / events from /my/notifications/ page."""
    items = []
    # Pattern for Drive2 notification feed items
    pattern = re.compile(r'<div[^>]*class=["\'][^"\']*c-notifications-item[^"\']*["\'][^>]*data-id=["\']([^"\']+)["\'][^>]*>(.*?)</div>\s*</div>', re.DOTALL | re.IGNORECASE)
    matches = pattern.findall(html)
    
    for item_id, content in matches[:10]:
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        items.append({"id": item_id, "text": clean_text})
        
    return items


async def check_user_drive2(user_id: int, bot: Bot, notify_if_no_change: bool = False) -> Tuple[bool, str]:
    """
    Checks Drive2.ru for new messages and notifications for a single user.
    """
    config = get_user_drive2_config(user_id)
    if not config or not config.get("enabled"):
        return False, "Мониторинг Drive2 выключен или не настроен."

    cookies_str = config.get("cookies", "").strip()
    profile_url = config.get("profile_url", "").strip()

    if not cookies_str and not profile_url:
        return False, "Не указаны данные для проверки Drive2 (куки или профиль)."

    headers = dict(DEFAULT_HEADERS)
    if cookies_str:
        headers["Cookie"] = cookies_str

    target_url = "https://www.drive2.ru/my/notifications/" if cookies_str else profile_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    logger.warning(f"Drive2 returned status {resp.status} for user {user_id}")
                    return False, f"Ошибка ответа Drive2.ru: HTTP {resp.status}"
                
                html = await resp.text()

                # Check if logged in when cookies were supplied
                if cookies_str and ("Войти" in html and "Зарегистрироваться" in html and "href=\"/my/" not in html):
                    return False, "⚠️ <b>Сессия Drive2 устарела!</b> Пожалуйста, обновите куки командой <code>/drive2_cookie</code>."

                cur_msgs, cur_notifs = await parse_drive2_counters(html)
                recent_items = await parse_recent_notification_items(html)
                
                prev_msgs = config.get("last_messages", 0)
                prev_notifs = config.get("last_notifications", 0)
                prev_event_ids = config.get("last_event_ids", [])

                new_event_ids = [it["id"] for it in recent_items] if recent_items else prev_event_ids
                
                has_new_events = False
                alert_parts = []

                # 1. New Private Messages
                if cur_msgs > prev_msgs:
                    has_new_events = True
                    diff = cur_msgs - prev_msgs
                    alert_parts.append(f"📩 <b>Новые личные сообщения:</b> +{diff} (всего непрочитанных: {cur_msgs})")

                # 2. New Notifications / Subscriptions / Likes
                if cur_notifs > prev_notifs:
                    has_new_events = True
                    diff = cur_notifs - prev_notifs
                    alert_parts.append(f"🔔 <b>Новые уведомления/подписки:</b> +{diff} (всего: {cur_notifs})")

                # 3. Check individual new feed items
                brand_new_items = [it for it in recent_items if it["id"] not in prev_event_ids]
                if brand_new_items:
                    has_new_events = True
                    alert_parts.append("\n📋 <b>Свежие события:</b>")
                    for it in brand_new_items[:3]:
                        alert_parts.append(f"• <i>{it['text']}</i>")

                # Update stored state
                update_drive2_state(
                    user_id,
                    messages_count=cur_msgs,
                    notifications_count=cur_notifs,
                    new_event_ids=new_event_ids
                )

                if has_new_events:
                    msg_text = (
                        "🚗 <b>Новое событие на Drive2.ru!</b> 🔔\n\n"
                        + "\n".join(alert_parts)
                        + "\n\n🔗 <a href='https://www.drive2.ru/my/notifications/'>Открыть уведомления на Drive2</a> | <a href='https://www.drive2.ru/my/messages/'>Личные сообщения</a>"
                    )
                    await bot.send_message(user_id, msg_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                    return True, "Обнаружены новые события!"
                
                if notify_if_no_change:
                    status_text = (
                        "🚗 <b>Статус Drive2.ru:</b> всё спокойно, новых событий нет.\n\n"
                        f"📩 Непрочитанных сообщений: <b>{cur_msgs}</b>\n"
                        f"🔔 Новых уведомлений: <b>{cur_notifs}</b>"
                    )
                    return True, status_text

                return True, "Изменений нет."

    except Exception as e:
        logger.error(f"Error checking Drive2 for user {user_id}: {e}")
        return False, f"Ошибка проверки Drive2: {e}"


async def check_all_drive2_users(bot: Bot) -> None:
    """Scheduled task that iterates over all configured users and checks for updates."""
    configs = load_drive2_configs()
    for uid_str, cfg in configs.items():
        if cfg.get("enabled") and (cfg.get("cookies") or cfg.get("profile_url")):
            try:
                user_id = int(uid_str)
                await check_user_drive2(user_id, bot, notify_if_no_change=False)
            except Exception as e:
                logger.warning(f"Error checking Drive2 loop for {uid_str}: {e}")
            await asyncio.sleep(2)
