import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("SmartHomeClient")

BASE_URL = "https://api.iot.yandex.net/v1.0"


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


async def get_user_info(token: str) -> Optional[Dict[str, Any]]:
    """Fetches full topology: households, rooms, devices, scenarios."""
    url = f"{BASE_URL}/user/info"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=_headers(token), timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning(f"Yandex IoT user/info returned status {resp.status}")
    except Exception as e:
        logger.error(f"Error fetching Yandex IoT user info: {e}")
    return None


async def get_device_by_name_or_id(token: str, query: str) -> Optional[Dict[str, Any]]:
    """Finds a device by its exact or partial name or ID."""
    info = await get_user_info(token)
    if not info:
        return None

    q_lower = query.strip().lower()
    devices = info.get("devices", [])

    # Exact ID match
    for d in devices:
        if d.get("id") == query:
            return d

    # Exact name match
    for d in devices:
        if d.get("name", "").strip().lower() == q_lower:
            return d

    # Partial name match
    for d in devices:
        if q_lower in d.get("name", "").strip().lower():
            return d

    return None


async def get_scenario_by_name_or_id(token: str, query: str) -> Optional[Dict[str, Any]]:
    """Finds a scenario by its exact or partial name or ID."""
    info = await get_user_info(token)
    if not info:
        return None

    q_lower = query.strip().lower()
    for s in info.get("scenarios", []):
        if s.get("id") == query or s.get("name", "").strip().lower() == q_lower or q_lower in s.get("name", "").strip().lower():
            return s
    return None


async def set_device_on_off(token: str, device_id: str, state: bool) -> Tuple[bool, str]:
    """Turns a device ON (True) or OFF (False)."""
    url = f"{BASE_URL}/devices/actions"
    payload = {
        "devices": [
            {
                "id": device_id,
                "actions": [
                    {
                        "type": "devices.capabilities.on_off",
                        "state": {
                            "instance": "on",
                            "value": state
                        }
                    }
                ]
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=_headers(token), timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status = data.get("status")
                    if status == "ok":
                        st_text = "включено" if state else "выключено"
                        return True, f"Устройство успешно {st_text}!"
                    return False, f"Статус выполнения: {status}"
                return False, f"Ошибка API: HTTP {resp.status}"
    except Exception as e:
        logger.error(f"Error setting device {device_id} state to {state}: {e}")
        return False, f"Ошибка отправки команды: {e}"


async def toggle_device_by_id(token: str, device_id: str, force_state: Optional[bool] = None) -> Tuple[bool, str, bool, str]:
    """Toggles or sets power for a device by its exact ID."""
    info = await get_user_info(token)
    if not info:
        return False, "Не удалось связаться с сервером Умного дома.", False, "Устройство"

    device = next((d for d in info.get("devices", []) if d.get("id") == device_id), None)
    if not device:
        return False, f"Устройство не найдено.", False, "Устройство"

    dev_name = device.get("name", "Прибор")
    current_state = False
    for cap in device.get("capabilities", []) or []:
        if cap.get("type") == "devices.capabilities.on_off":
            c_state = cap.get("state") or {}
            current_state = bool(c_state.get("value", False))

    target_state = (not current_state) if force_state is None else force_state
    ok, msg = await set_device_on_off(token, device_id, target_state)
    if ok:
        state_icon = "🟢 Включено" if target_state else "⚪️ Выключено"
        return True, f"✅ {dev_name}: {state_icon}", target_state, dev_name
    return False, f"❌ {dev_name}: {msg}", current_state, dev_name


async def toggle_device_by_name(token: str, name_query: str, force_state: Optional[bool] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Toggles or sets power for a device by name."""
    dev = await get_device_by_name_or_id(token, name_query)
    if not dev:
        return False, f"Устройство «{name_query}» не найдено в вашем умном доме.", None

    dev_id = dev["id"]
    dev_name = dev["name"]

    current_state = False
    for cap in dev.get("capabilities", []):
        if cap.get("type") == "devices.capabilities.on_off":
            c_state = cap.get("state") or {}
            current_state = bool(c_state.get("value", False))

    target_state = (not current_state) if force_state is None else force_state
    ok, msg = await set_device_on_off(token, dev_id, target_state)
    
    if ok:
        state_icon = "🟢 Включено" if target_state else "⚪️ Выключено"
        return True, f"✅ <b>{dev_name}:</b> {state_icon}", dev
    return False, f"❌ Ошибка переключения <b>{dev_name}</b>: {msg}", dev


async def execute_scenario(token: str, scenario_id_or_name: str) -> Tuple[bool, str]:
    """Executes a Yandex IoT scenario."""
    sc = await get_scenario_by_name_or_id(token, scenario_id_or_name)
    if not sc:
        return False, f"Сценарий «{scenario_id_or_name}» не найден."

    sc_id = sc["id"]
    sc_name = sc["name"]
    url = f"{BASE_URL}/scenarios/{sc_id}/actions"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=_headers(token), timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    return True, f"🎬 Сценарий <b>«{sc_name}»</b> успешно запущен!"
                return False, f"Ошибка запуска сценария: HTTP {resp.status}"
    except Exception as e:
        logger.error(f"Error executing scenario {sc_id}: {e}")
        return False, f"Ошибка запуска: {e}"


async def turn_off_all_lights(token: str) -> Tuple[bool, str, int]:
    """Finds all lights/switches that are currently ON and turns them all OFF."""
    info = await get_user_info(token)
    if not info:
        return False, "Не удалось получить список устройств.", 0

    to_turn_off = []
    for d in info.get("devices", []):
        d_type = d.get("type", "")
        if any(t in d_type for t in ["light", "switch", "socket", "openable"]):
            for cap in d.get("capabilities", []):
                if cap.get("type") == "devices.capabilities.on_off":
                    c_state = cap.get("state") or {}
                    if c_state.get("value") is True:
                        to_turn_off.append(d["id"])

    if not to_turn_off:
        return True, "✨ Весь свет и приборы уже выключены!", 0

    url = f"{BASE_URL}/devices/actions"
    payload = {
        "devices": [
            {
                "id": dev_id,
                "actions": [
                    {
                        "type": "devices.capabilities.on_off",
                        "state": {
                            "instance": "on",
                            "value": False
                        }
                    }
                ]
            }
            for dev_id in to_turn_off
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=_headers(token), timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return True, f"💡 Выключено приборов/ламп: <b>{len(to_turn_off)} шт.</b>", len(to_turn_off)
                return False, f"Ошибка выключения: HTTP {resp.status}", 0
    except Exception as e:
        logger.error(f"Error turning off all lights: {e}")
        return False, f"Ошибка: {e}", 0


async def turn_off_room_devices(token: str, room_id: str) -> Tuple[bool, str, int]:
    """Turns off all active devices in a specific room."""
    info = await get_user_info(token)
    if not info:
        return False, "Не удалось получить список устройств.", 0

    to_turn_off = []
    for d in info.get("devices", []):
        if d.get("room") == room_id:
            for cap in d.get("capabilities", []):
                if cap.get("type") == "devices.capabilities.on_off":
                    c_state = cap.get("state") or {}
                    if c_state.get("value") is True:
                        to_turn_off.append(d["id"])

    if not to_turn_off:
        return True, "✨ В этой комнате все приборы уже выключены!", 0

    url = f"{BASE_URL}/devices/actions"
    payload = {
        "devices": [
            {
                "id": dev_id,
                "actions": [
                    {
                        "type": "devices.capabilities.on_off",
                        "state": {
                            "instance": "on",
                            "value": False
                        }
                    }
                ]
            }
            for dev_id in to_turn_off
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=_headers(token), timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return True, f"💡 В комнате выключено приборов: <b>{len(to_turn_off)} шт.</b>", len(to_turn_off)
                return False, f"Ошибка выключения: HTTP {resp.status}", 0
    except Exception as e:
        logger.error(f"Error turning off room devices: {e}")
        return False, f"Ошибка: {e}", 0


async def build_smart_home_card(token: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Builds a structured status overview of rooms, climate, security sensors and active devices."""
    info = await get_user_info(token)
    if not info:
        return False, "⚠️ Не удалось связаться с сервером Умного дома Яндекса.", {}

    rooms = {r["id"]: r["name"] for r in info.get("rooms", [])}
    devices = info.get("devices", [])
    scenarios = info.get("scenarios", [])

    climate_data = []
    active_devices = []
    security_alerts = []
    door_states = []

    priority_states = {
        "corridor_switch": False,
        "bathroom_light": False,
        "exhaust_fan": False,
        "floor_heating": False,
        "living_light": False,
        "bar_counter": False
    }

    for d in devices:
        d_name = d.get("name", "")
        r_name = rooms.get(d.get("room"), "")

        # Check properties (Climate, Leak, Door)
        for prop in d.get("properties", []) or []:
            p_state = prop.get("state") or {}
            p_val = p_state.get("value")
            inst = prop.get("parameters", {}).get("instance", "")
            
            if inst == "temperature" and p_val is not None:
                climate_data.append(f"• <b>{r_name or d_name}</b>: 🌡 <b>{round(float(p_val), 1)}°C</b>")
            elif inst == "humidity" and p_val is not None:
                if climate_data:
                    climate_data[-1] += f", 💧 <b>{round(float(p_val))}%</b>"
            elif inst == "water_leak":
                if p_val == "leak":
                    security_alerts.append(f"🚨 <b>ВНИМАНИЕ: Протечка воды ({r_name})!</b>")
            elif inst == "open":
                st = "🚪 Открыто" if p_val == "opened" else "🔒 Закрыто"
                door_states.append(f"• {d_name} ({r_name}): <b>{st}</b>")

        # Check capabilities (On/Off power)
        for cap in d.get("capabilities", []) or []:
            if cap.get("type") == "devices.capabilities.on_off":
                c_state = cap.get("state") or {}
                is_on = bool(c_state.get("value", False))
                if is_on:
                    active_devices.append(f"• {d_name} <i>({r_name})</i>")

                # Track priority device states
                d_name_low = d_name.lower()
                if "выключатель коридор" in d_name_low or "свет коридор" in d_name_low:
                    priority_states["corridor_switch"] = is_on
                elif "свет в ванной" in d_name_low or "свет ванная" in d_name_low:
                    priority_states["bathroom_light"] = is_on
                elif "вытяжка" in d_name_low:
                    priority_states["exhaust_fan"] = is_on
                elif "теплый пол" in d_name_low or "тёплый пол" in d_name_low:
                    priority_states["floor_heating"] = is_on

    # Text formatting
    parts = ["🏠 <b>Управление Умным Домом (Яндекс / Алиса):</b>\n"]

    if security_alerts:
        parts.append("\n" + "\n".join(security_alerts) + "\n")
    else:
        parts.append("🛡️ <b>Безопасность:</b> ✅ Протечек нет, датчики в норме.\n")

    if door_states:
        parts.append("🚪 <b>Двери:</b>\n" + "\n".join(door_states) + "\n")

    if climate_data:
        parts.append("🌡 <b>Микроклимат дома:</b>\n" + "\n".join(climate_data) + "\n")

    if active_devices:
        parts.append(f"⚡ <b>Включено прямо сейчас ({len(active_devices)}):</b>\n" + "\n".join(active_devices[:8]))
        if len(active_devices) > 8:
            parts.append(f"<i>...и ещё {len(active_devices) - 8} приборов</i>")
    else:
        parts.append("✨ <i>Все приборы и свет выключены.</i>")

    return True, "\n".join(parts), {
        "priority_states": priority_states,
        "devices_count": len(devices),
        "active_count": len(active_devices),
        "scenarios": scenarios
    }
