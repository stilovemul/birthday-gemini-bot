import asyncio
import logging
import json
import struct
from typing import Dict, Any, Optional, Tuple, List
from aiogram import Bot
from aiogram.enums import ParseMode

from modules.max_tracker.storage import (
    load_max_configs,
    get_user_max_config,
    update_max_state
)

logger = logging.getLogger("MAXChecker")

WS_URL = "wss://api.oneme.ru/websocket"
APP_VERSION = "26.8.10"


def lz4_decompress_block(src: bytes, uncompressed_size: int) -> bytes:
    """Pure-Python LZ4 block decompressor matching oneme / web.max.ru framing."""
    dst = bytearray(uncompressed_size)
    src_len = len(src)
    src_idx = 0
    dst_idx = 0

    while src_idx < src_len:
        token = src[src_idx]
        src_idx += 1

        literal_len = token >> 4
        if literal_len == 15:
            while src_idx < src_len:
                b = src[src_idx]
                src_idx += 1
                literal_len += b
                if b != 255:
                    break

        dst[dst_idx:dst_idx + literal_len] = src[src_idx:src_idx + literal_len]
        src_idx += literal_len
        dst_idx += literal_len

        if src_idx >= src_len:
            break

        offset = src[src_idx] | (src[src_idx + 1] << 8)
        src_idx += 2

        match_len = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while src_idx < src_len:
                b = src[src_idx]
                src_idx += 1
                match_len += b
                if b != 255:
                    break

        match_pos = dst_idx - offset
        for _ in range(match_len):
            dst[dst_idx] = dst[match_pos]
            dst_idx += 1
            match_pos += 1

    return bytes(dst[:dst_idx])


def encode_max_packet(cmd: int, seq: int, opcode: int, payload: dict = None) -> bytes:
    """Encodes MAX protocol packet with 10-byte binary header and MsgPack payload."""
    import msgpack
    payload_bytes = msgpack.packb(payload) if payload is not None else b""
    plen = len(payload_bytes)
    hdr = bytearray(10)
    hdr[0] = 10  # Proto version
    hdr[1] = cmd
    struct.pack_into(">h", hdr, 2, seq)
    struct.pack_into(">h", hdr, 4, opcode)
    hdr[6] = 0   # Uncompressed
    hdr[7] = (plen >> 16) & 0xFF
    hdr[8] = (plen >> 8) & 0xFF
    hdr[9] = plen & 0xFF
    return bytes(hdr) + payload_bytes


def decode_max_packet(data: bytes) -> Optional[Dict[str, Any]]:
    """Decodes MAX binary packet with LZ4 and MsgPack support."""
    import msgpack
    if len(data) < 10:
        return None
    magic = data[0]
    cmd = data[1]
    seq, opcode = struct.unpack_from(">hh", data, 2)
    comp = data[6]
    plen = (data[7] << 16) | (data[8] << 8) | data[9]
    payload_raw = data[10:10 + plen]

    if comp > 0:
        uncomp_size = plen * comp
        payload_raw = lz4_decompress_block(payload_raw, uncomp_size)

    payload = msgpack.unpackb(payload_raw, raw=False, strict_map_key=False) if payload_raw else None
    return {"cmd": cmd, "seq": seq, "opcode": opcode, "payload": payload}


async def fetch_max_updates(token: str, viewer_id: str = "") -> Tuple[bool, Dict[str, Any], str]:
    """
    Connects to MAX via WebSocket, authenticates with token, and fetches unread message counts.
    """
    if not token:
        return False, {}, "Токен MAX не указан."

    clean_token = token.strip()
    if clean_token.startswith("{") and "token" in clean_token:
        try:
            parsed = json.loads(clean_token)
            clean_token = parsed.get("token", clean_token)
        except Exception:
            pass

    try:
        import websockets
        async with websockets.connect(
            WS_URL,
            origin="https://web.max.ru",
            additional_headers={"User-Agent": "Mozilla/5.0 Chrome/124.0.0.0 Safari/537.36"},
            open_timeout=8,
            close_timeout=4
        ) as ws:
            # 1. Handshake Init (opcode 6)
            init_pkt = encode_max_packet(0, 0, 6, {
                "userAgent": {
                    "deviceType": "WEB",
                    "pushDeviceType": "WEBPUSH",
                    "locale": "ru",
                    "deviceLocale": "ru",
                    "osVersion": "Windows",
                    "deviceName": "Chrome",
                    "appVersion": APP_VERSION
                },
                "deviceId": "d41d8cd98f00b204e9800998ecf8427e"
            })
            await ws.send(init_pkt)
            await asyncio.wait_for(ws.recv(), timeout=5)

            # 2. Login (opcode 19)
            login_pkt = encode_max_packet(0, 1, 19, {"token": clean_token})
            await ws.send(login_pkt)

            resp_raw = await asyncio.wait_for(ws.recv(), timeout=6)
            decoded = decode_max_packet(resp_raw)
            if not decoded or not decoded.get("payload"):
                return False, {}, "Некорректный ответ от сервера MAX."

            p = decoded["payload"]
            chats = p.get("chats", [])
            profile = p.get("profile", {})
            names = profile.get("contact", {}).get("names", [])
            first_name = names[0].get("name", "Олег") if names else "Олег"

            unread_chats = 0
            unread_messages = 0
            details = []

            for c in chats:
                u_cnt = c.get("unreadCount", c.get("unread", 0))
                if u_cnt > 0:
                    unread_chats += 1
                    unread_messages += u_cnt
                    title = c.get("title", c.get("name", "Диалог"))
                    last_msg = c.get("lastMessage", {})
                    text = last_msg.get("text", "") if isinstance(last_msg, dict) else ""
                    details.append({
                        "title": title,
                        "unread": u_cnt,
                        "text": text[:60]
                    })

            return True, {
                "user_name": first_name,
                "unread_messages": unread_messages,
                "unread_chats": unread_chats,
                "total_chats": len(chats),
                "details": details
            }, "OK"

    except Exception as e:
        logger.error(f"MAX WebSocket fetch error: {e}")
        return False, {}, f"Ошибка подключения к MAX: {e}"


async def check_max_for_user(user_id: int, bot: Bot, notify_only_new: bool = True) -> Optional[str]:
    """Checks MAX messenger events for a specific user."""
    config = get_user_max_config(user_id)
    if not config or not config.get("enabled", True):
        return None

    token = config.get("token", "").strip()
    viewer_id = config.get("viewer_id", "").strip()
    if not token:
        return None

    last_msg = config.get("last_messages", 0)
    last_chats = config.get("last_unread_chats", 0)

    success, data, err_info = await fetch_max_updates(token, viewer_id)
    if not success:
        logger.warning(f"MAX check failed for user {user_id}: {err_info}")
        return None

    cur_msgs = data.get("unread_messages", 0)
    cur_chats = data.get("unread_chats", 0)
    total_chats = data.get("total_chats", 0)
    user_name = data.get("user_name", "Олег")
    details = data.get("details", [])

    new_msgs = max(0, cur_msgs - last_msg) if cur_msgs > last_msg else 0

    update_max_state(
        user_id=user_id,
        messages_count=cur_msgs,
        unread_chats_count=cur_chats
    )

    if new_msgs > 0 and notify_only_new:
        alert_lines = [
            "💬🔔 <b>Новые сообщения в мессенджере MAX (web.max.ru):</b>\n",
            f"✉️ Новых входящих: <b>+{new_msgs}</b> (всего непрочитанных: {cur_msgs})"
        ]
        if details:
            alert_lines.append("\n📋 <b>Свежие диалоги:</b>")
            for d in details[:3]:
                alert_lines.append(f"• <b>{d['title']}:</b> <i>{d['text']}</i> (+{d['unread']})")

        alert_lines.append("\n👉 <a href='https://web.max.ru/'>Открыть web.max.ru</a>")
        alert_text = "\n".join(alert_lines)

        try:
            await bot.send_message(user_id, alert_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            logger.info(f"MAX Push notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send MAX push to user {user_id}: {e}")

    detail_lines = []
    if details:
        detail_lines.append("\n📋 <b>Непрочитанные диалоги:</b>")
        for d in details:
            detail_lines.append(f"• <b>{d['title']}</b>: <i>{d['text']}</i> (+{d['unread']})")

    status_report = (
        f"💬 <b>Центр мониторинга MAX ({user_name})</b>\n\n"
        "📊 <b>Состояние:</b> 🟢 Активен (проверка каждые 60с)\n"
        f"💬 <b>Всего активных чатов:</b> {total_chats}\n\n"
        "📬 <b>Текущие счетчики:</b>\n"
        f"• ✉️ Непрочитанных сообщений: <b>{cur_msgs}</b>\n"
        f"• 💬 Чатов с новыми сообщениями: <b>{cur_chats}</b>\n"
        + "\n".join(detail_lines) + "\n\n"
        + ("✨ <i>Все сообщения прочитаны!</i>" if cur_msgs == 0 else "⚡ <i>Есть новые входящие в MAX!</i>")
        + "\n\n🔗 <a href='https://web.max.ru/'>Открыть web.max.ru</a>"
    )
    return status_report


async def check_all_max_users(bot: Bot) -> None:
    """Iterates through all users in background every 60s."""
    configs = load_max_configs()
    for uid_str, cfg in configs.items():
        if cfg.get("enabled", True) and cfg.get("token"):
            try:
                await check_max_for_user(int(uid_str), bot, notify_only_new=True)
            except Exception as e:
                logger.warning(f"Error checking MAX for user {uid_str}: {e}")
            await asyncio.sleep(1.5)
