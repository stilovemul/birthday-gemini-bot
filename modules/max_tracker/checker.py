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


def ext_to_hex(val: Any) -> str:
    if hasattr(val, "data"):
        return val.data.hex()
    if isinstance(val, bytes):
        return val.hex()
    return str(val)


async def fetch_max_updates(token: str, viewer_id: str = "") -> Tuple[bool, Dict[str, Any], str]:
    """
    Connects to MAX via WebSocket, authenticates with token, and fetches chats and latest incoming messages.
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
            contacts = p.get("contacts", [])
            profile = p.get("profile", {})
            my_contact = profile.get("contact", {})
            my_id_raw = my_contact.get("id")
            my_id_hex = ext_to_hex(my_id_raw) if my_id_raw else ""

            # Build contacts directory
            contact_names = {}
            for ct in contacts:
                cid = ext_to_hex(ct.get("id"))
                c_names = ct.get("names", [])
                c_name = c_names[0].get("name") if c_names else ct.get("phone", "Собеседник")
                contact_names[cid] = c_name

            names = my_contact.get("names", [])
            first_name = names[0].get("name", "Олег") if names else "Олег"

            recent_messages = []
            unread_chats = 0
            unread_messages = 0

            for c in chats:
                c_title = c.get("title") or c.get("name")
                c_id_hex = ext_to_hex(c.get("id"))
                last_msg = c.get("lastMessage")
                
                # Resolve partner name from participants/members
                recipients = [ext_to_hex(x) for x in c.get("participants", []) or c.get("members", []) or []]
                partner_name = ""
                for r in recipients:
                    if r != my_id_hex and r in contact_names:
                        partner_name = contact_names[r]
                        break

                if isinstance(last_msg, dict):
                    sender_raw = last_msg.get("sender")
                    sender_hex = ext_to_hex(sender_raw)
                    msg_id_raw = last_msg.get("id")
                    msg_id_hex = ext_to_hex(msg_id_raw)
                    msg_text = last_msg.get("text", "")
                    
                    is_incoming = (sender_hex != my_id_hex)
                    sender_display = contact_names.get(sender_hex, "Собеседник") if is_incoming else "Вы"

                    if not c_title:
                        if partner_name:
                            c_title = partner_name
                        elif is_incoming and sender_display != "Собеседник":
                            c_title = sender_display
                        else:
                            c_title = "Личный диалог"

                    recent_messages.append({
                        "chat_id": c_id_hex,
                        "title": c_title,
                        "msg_id": msg_id_hex,
                        "is_incoming": is_incoming,
                        "sender_name": sender_display,
                        "text": msg_text[:80]
                    })

            return True, {
                "user_name": first_name,
                "unread_messages": unread_messages,
                "unread_chats": unread_chats,
                "total_chats": len(chats),
                "recent_messages": recent_messages
            }, "OK"

    except Exception as e:
        logger.error(f"MAX WebSocket fetch error: {e}")
        return False, {}, f"Ошибка подключения к MAX: {e}"


async def check_max_for_user(user_id: int, bot: Bot, notify_only_new: bool = True) -> Optional[str]:
    """Checks MAX messenger events for a specific user and sends instant notifications for new incoming messages."""
    config = get_user_max_config(user_id)
    if not config or not config.get("enabled", True):
        return None

    token = config.get("token", "").strip()
    viewer_id = config.get("viewer_id", "").strip()
    if not token:
        return None

    seen_ids = set(config.get("last_event_ids", []))
    is_initial_run = (len(seen_ids) == 0)

    success, data, err_info = await fetch_max_updates(token, viewer_id)
    if not success:
        logger.warning(f"MAX check failed for user {user_id}: {err_info}")
        return None

    user_name = data.get("user_name", "Олег")
    total_chats = data.get("total_chats", 0)
    recent_msgs = data.get("recent_messages", [])

    new_incoming = []
    current_all_ids = []

    for m in recent_msgs:
        m_id = m.get("msg_id")
        if m_id:
            current_all_ids.append(m_id)
            if m.get("is_incoming"):
                if m_id not in seen_ids and not is_initial_run:
                    new_incoming.append(m)

    # Update seen message IDs (keep up to 100 recent)
    updated_seen = list(set(current_all_ids + list(seen_ids)))[-100:]
    update_max_state(
        user_id=user_id,
        messages_count=len(new_incoming),
        unread_chats_count=len(new_incoming),
        event_ids=updated_seen
    )

    import html
    if new_incoming and notify_only_new:
        alert_lines = [
            f"💬🔔 <b>Новое сообщение в MAX (web.max.ru)!</b>\n"
        ]
        for m in new_incoming[:5]:
            chat_name = html.escape(str(m.get("title", "Диалог")))
            msg_snippet = html.escape(str(m.get("text", "")))
            if not msg_snippet:
                msg_snippet = "📷 [Вложение / Фото / Файл]"
            alert_lines.append(f"👤 <b>{chat_name}:</b>\n<i>«{msg_snippet}»</i>\n")

        alert_lines.append("👉 <a href='https://web.max.ru/'>Открыть web.max.ru</a>")
        alert_text = "\n".join(alert_lines)

        try:
            await bot.send_message(user_id, alert_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            logger.info(f"MAX Push notification sent to user {user_id} ({len(new_incoming)} msgs)")
        except Exception as e:
            logger.error(f"Failed to send MAX push to user {user_id}: {e}")

    recent_display = []
    for m in recent_msgs[:4]:
        ic = "📥" if m.get("is_incoming") else "📤"
        t_raw = m.get("text") or "📷 [Вложение]"
        title_esc = html.escape(str(m.get("title", "Диалог")))
        text_esc = html.escape(str(t_raw[:50]))
        recent_display.append(f"{ic} <b>{title_esc}:</b> <i>{text_esc}</i>")

    status_report = (
        f"💬 <b>Центр мониторинга MAX ({html.escape(str(user_name))})</b>\n\n"
        "📊 <b>Состояние:</b> 🟢 Активен (проверка каждые 60с)\n"
        f"💬 <b>Всего активных чатов:</b> {total_chats}\n\n"
        "📬 <b>Последние диалоги:</b>\n"
        + ("\n".join(recent_display) if recent_display else "• <i>Диалогов нет</i>")
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
