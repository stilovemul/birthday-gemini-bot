import logging
import asyncio
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core.keyboards import get_main_menu
from modules.smart_home.storage import get_user_smart_home_config, set_user_smart_home_token
from modules.smart_home.client import (
    build_smart_home_card,
    toggle_device_by_name,
    toggle_device_by_id,
    execute_scenario,
    turn_off_all_lights,
    turn_off_room_devices,
    get_user_info
)

logger = logging.getLogger("SmartHomeHandler")
router = Router(name="smart_home")


def get_smart_home_keyboard(priority_states: dict) -> InlineKeyboardMarkup:
    corr_st = "🟢" if priority_states.get("corridor_switch") else "⚪️"
    bath_st = "🟢" if priority_states.get("bathroom_light") else "⚪️"
    fan_st = "🟢" if priority_states.get("exhaust_fan") else "⚪️"
    floor_st = "🟢" if priority_states.get("floor_heating") else "⚪️"

    keyboard = [
        [
            InlineKeyboardButton(text=f"🚪 Свет коридор {corr_st}", callback_data="sh_toggle_corridor"),
            InlineKeyboardButton(text=f"🛁 Свет ванная {bath_st}", callback_data="sh_toggle_bath")
        ],
        [
            InlineKeyboardButton(text=f"💨 Вытяжка {fan_st}", callback_data="sh_toggle_fan"),
            InlineKeyboardButton(text=f"♨️ Тёплый пол {floor_st}", callback_data="sh_toggle_floor")
        ],
        [
            InlineKeyboardButton(text="🛋 Свет в гостиной", callback_data="sh_scen_living"),
            InlineKeyboardButton(text="🍸 Барная стойка", callback_data="sh_scen_bar")
        ],
        [
            InlineKeyboardButton(text="🎛 Все приборы и тумблеры (35)", callback_data="sh_all_toggles_0")
        ],
        [
            InlineKeyboardButton(text="🚪 По комнатам", callback_data="sh_rooms_menu"),
            InlineKeyboardButton(text="🎬 Сценарии", callback_data="sh_scenarios_list")
        ],
        [
            InlineKeyboardButton(text="💡 Выключить весь свет ⚪️", callback_data="sh_turn_off_all"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="sh_refresh")
        ],
        [
            InlineKeyboardButton(text="📱 Открыть Mini App (Дашборд)", web_app=WebAppInfo(url="https://birthday-gemini-bot.onrender.com/app"))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _get_device_icon(name: str, d_type: str) -> str:
    n = name.lower()
    if "ванн" in n or "душ" in n:
        return "🛁"
    if "вытяжк" in n or "вентил" in n:
        return "💨"
    if "пол" in n or "тёплый" in n or "теплый" in n:
        return "♨️"
    if "коридор" in n or "прихож" in n:
        return "🚪"
    if "кухн" in n or "фартук" in n or "стол" in n or "барн" in n:
        return "🍳"
    if "гостин" in n or "диван" in n:
        return "🛋"
    if "спальн" in n or "кроват" in n or "бра" in n:
        return "🛏"
    if "розетк" in n or "socket" in d_type:
        return "🔌"
    if "свет" in n or "люстр" in n or "спот" in n or "ламп" in n or "light" in d_type:
        return "💡"
    return "⚡"


def build_all_devices_keyboard(info: dict, page: int = 0, per_page: int = 8) -> tuple[str, InlineKeyboardMarkup]:
    """Generates an interactive matrix of on/off toggle buttons for all controllable devices with pagination."""
    devices = info.get("devices", [])
    rooms = {r["id"]: r["name"] for r in info.get("rooms", [])}

    controllable = []
    for d in devices:
        has_on_off = False
        is_on = False
        for cap in d.get("capabilities", []) or []:
            if cap.get("type") == "devices.capabilities.on_off":
                has_on_off = True
                c_val = (cap.get("state") or {}).get("value")
                is_on = bool(c_val)
        if has_on_off:
            r_name = rooms.get(d.get("room"), "Дом")
            icon = _get_device_icon(d.get("name", ""), d.get("type", ""))
            controllable.append({
                "id": d["id"],
                "name": d.get("name", "Прибор"),
                "room": r_name,
                "is_on": is_on,
                "icon": icon
            })

    total = len(controllable)
    if total == 0:
        text = "⚠️ Управляемые приборы не найдены."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="sh_refresh")]])
        return text, kb

    # Sort: Active first, then by room/name
    controllable.sort(key=lambda x: (not x["is_on"], x["room"], x["name"]))

    max_pages = max(1, (total + per_page - 1) // per_page)
    page = max(0, min(page, max_pages - 1))
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total)
    current_batch = controllable[start_idx:end_idx]

    active_count = sum(1 for d in controllable if d["is_on"])

    text = f"🎛 <b>Все приборы и тумблеры Умного Дома:</b>\n\n💡 Всего устройств: <b>{total} шт.</b> | Включено прямо сейчас: <b>{active_count} шт.</b>\n<i>Нажмите на любой прибор, чтобы мгновенно включить или выключить его:</i>"

    kb_rows = []
    row = []
    for d in current_batch:
        st_icon = "🟢" if d["is_on"] else "⚪️"
        d_name = d["name"]
        if len(d_name) > 18:
            d_name = d_name[:16] + ".."
        btn_text = f"{d['icon']} {d_name} {st_icon}"
        cb_data = f"sh_t_{d['id']}_{page}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=cb_data))
        if len(row) == 2:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)

    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"sh_all_toggles_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1}/{max_pages}", callback_data=f"sh_all_toggles_{page}"))
    if page < max_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"sh_all_toggles_{page + 1}"))
    if nav_row:
        kb_rows.append(nav_row)

    # Actions row
    kb_rows.append([
        InlineKeyboardButton(text="💡 Выключить весь свет ⚪️", callback_data=f"sh_turn_off_all_from_tog_{page}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"sh_all_toggles_{page}")
    ])
    kb_rows.append([
        InlineKeyboardButton(text="🚪 По комнатам", callback_data="sh_rooms_menu"),
        InlineKeyboardButton(text="🔙 Главная панель", callback_data="sh_refresh")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=kb_rows)


def build_rooms_menu_keyboard(info: dict) -> tuple[str, InlineKeyboardMarkup]:
    rooms = info.get("rooms", [])
    devices = info.get("devices", [])

    text = "🚪 <b>Выберите комнату для управления приборами:</b>\n\nВ каждой комнате доступны персональные тумблеры и кнопка выключения света."
    kb_rows = []
    
    row = []
    for r in rooms:
        r_id = r["id"]
        r_name = r["name"]
        r_devs = [d for d in devices if d.get("room") == r_id]
        controllable_in_room = 0
        active_in_room = 0
        for d in r_devs:
            for cap in d.get("capabilities", []) or []:
                if cap.get("type") == "devices.capabilities.on_off":
                    controllable_in_room += 1
                    if (cap.get("state") or {}).get("value"):
                        active_in_room += 1
        
        if controllable_in_room > 0:
            st_badge = f" ({active_in_room} 🟢)" if active_in_room > 0 else " (⚪️)"
            btn_text = f"🏠 {r_name}{st_badge}"
            row.append(InlineKeyboardButton(text=btn_text, callback_data=f"sh_room_{r_id}"))
            if len(row) == 2:
                kb_rows.append(row)
                row = []
    if row:
        kb_rows.append(row)

    kb_rows.append([
        InlineKeyboardButton(text="🎛 Все приборы общим списком", callback_data="sh_all_toggles_0")
    ])
    kb_rows.append([
        InlineKeyboardButton(text="🔙 Назад к главной панели", callback_data="sh_refresh")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=kb_rows)


def build_room_devices_keyboard(info: dict, room_id: str) -> tuple[str, InlineKeyboardMarkup]:
    rooms = {r["id"]: r["name"] for r in info.get("rooms", [])}
    r_name = rooms.get(room_id, "Комната")
    devices = [d for d in info.get("devices", []) if d.get("room") == room_id]

    controllable = []
    climate_lines = []

    for d in devices:
        for prop in d.get("properties", []) or []:
            p_val = (prop.get("state") or {}).get("value")
            inst = prop.get("parameters", {}).get("instance", "")
            if inst == "temperature" and p_val is not None:
                climate_lines.append(f"🌡 Температура: <b>{p_val}°C</b>")
            elif inst == "humidity" and p_val is not None:
                climate_lines.append(f"💧 Влажность: <b>{p_val}%</b>")

        for cap in d.get("capabilities", []) or []:
            if cap.get("type") == "devices.capabilities.on_off":
                is_on = bool((cap.get("state") or {}).get("value"))
                icon = _get_device_icon(d.get("name", ""), d.get("type", ""))
                controllable.append({
                    "id": d["id"],
                    "name": d.get("name", "Прибор"),
                    "is_on": is_on,
                    "icon": icon
                })

    clim_text = "\n" + " | ".join(climate_lines) if climate_lines else ""
    active_count = sum(1 for d in controllable if d["is_on"])
    text = f"🏠 <b>Комната: {r_name}</b>{clim_text}\n\nУправляемых приборов: <b>{len(controllable)}</b> | Включено: <b>{active_count}</b>\n<i>Нажимайте на тумблеры для переключения:</i>"

    kb_rows = []
    row = []
    for d in controllable:
        st_icon = "🟢" if d["is_on"] else "⚪️"
        btn_text = f"{d['icon']} {d['name']} {st_icon}"
        cb_data = f"sh_tr_{room_id}_{d['id']}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=cb_data))
        if len(row) == 2:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)

    kb_rows.append([
        InlineKeyboardButton(text="💡 Выключить всё в комнате ⚪️", callback_data=f"sh_room_off_{room_id}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"sh_room_{room_id}")
    ])
    kb_rows.append([
        InlineKeyboardButton(text="🔙 К списку комнат", callback_data="sh_rooms_menu"),
        InlineKeyboardButton(text="🏠 Главная панель", callback_data="sh_refresh")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=kb_rows)


@router.message(Command("home"))
@router.message(Command("smarthome"))
@router.message(F.text == "🏠 Умный дом")
async def cmd_smart_home(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    config = get_user_smart_home_config(user_id)
    token = config.get("token", "") if config else ""

    if not token:
        await message.answer(
            "🏠 <b>Умный дом Яндекса не подключен.</b>\n\n"
            "Отправьте токен командой:\n<code>/iot_token ВАШ_ТОКЕН</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ok, report, meta = await build_smart_home_card(token)

    if not ok:
        await message.answer(f"⚠️ {report}", reply_markup=get_main_menu())
        return

    kb = get_smart_home_keyboard(meta.get("priority_states", {}))
    await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data.startswith("sh_"))
async def handle_smart_home_callbacks(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    config = get_user_smart_home_config(user_id)
    token = config.get("token", "") if config else ""

    if not token:
        await callback.answer("⚠️ Токен Умного дома не настроен.", show_alert=True)
        return

    action = callback.data

    # 1. Main Dashboard Refresh
    if action == "sh_refresh":
        await callback.answer("🔄 Обновляю панель...")
        ok, report, meta = await build_smart_home_card(token)
        if ok:
            kb = get_smart_home_keyboard(meta.get("priority_states", {}))
            try:
                await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        return

    # 2. All Devices Matrix with Pagination
    if action.startswith("sh_all_toggles_"):
        page_str = action.replace("sh_all_toggles_", "")
        page = int(page_str) if page_str.isdigit() else 0
        info = await get_user_info(token)
        if info:
            text, kb = build_all_devices_keyboard(info, page=page)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        await callback.answer()
        return

    # 3. Toggle Individual Device in All Devices View
    if action.startswith("sh_t_"):
        # Format: sh_t_{dev_id}_{page}
        parts = action.replace("sh_t_", "").split("_")
        dev_id = parts[0]
        page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

        ok, toast_msg, new_st, d_name = await toggle_device_by_id(token, dev_id)
        await callback.answer(f"💡 {d_name}: {'Включено 🟢' if new_st else 'Выключено ⚪️'}", show_alert=False)

        await asyncio.sleep(0.3)
        info = await get_user_info(token)
        if info:
            text, kb = build_all_devices_keyboard(info, page=page)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        return

    # 4. Rooms Menu
    if action == "sh_rooms_menu":
        info = await get_user_info(token)
        if info:
            text, kb = build_rooms_menu_keyboard(info)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        await callback.answer()
        return

    # 5. Room Specific View
    if action.startswith("sh_room_") and not action.startswith("sh_room_off_"):
        room_id = action.replace("sh_room_", "")
        info = await get_user_info(token)
        if info:
            text, kb = build_room_devices_keyboard(info, room_id)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        await callback.answer()
        return

    # 6. Toggle Device in Room View
    if action.startswith("sh_tr_"):
        # Format: sh_tr_{room_id}_{dev_id}
        parts = action.replace("sh_tr_", "").split("_", 1)
        room_id = parts[0]
        dev_id = parts[1] if len(parts) > 1 else ""

        ok, toast_msg, new_st, d_name = await toggle_device_by_id(token, dev_id)
        await callback.answer(f"💡 {d_name}: {'Включено 🟢' if new_st else 'Выключено ⚪️'}", show_alert=False)

        await asyncio.sleep(0.3)
        info = await get_user_info(token)
        if info:
            text, kb = build_room_devices_keyboard(info, room_id)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        return

    # 7. Turn Off All Devices in Room
    if action.startswith("sh_room_off_"):
        room_id = action.replace("sh_room_off_", "")
        ok, msg, count = await turn_off_room_devices(token, room_id)
        await callback.answer(f"💡 Выключено: {count} шт.", show_alert=False)

        await asyncio.sleep(0.5)
        info = await get_user_info(token)
        if info:
            text, kb = build_room_devices_keyboard(info, room_id)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        return

    # 8. Turn Off All Lights from All Toggles View
    if action.startswith("sh_turn_off_all_from_tog_"):
        page_str = action.replace("sh_turn_off_all_from_tog_", "")
        page = int(page_str) if page_str.isdigit() else 0
        ok, msg, count = await turn_off_all_lights(token)
        await callback.answer(f"💡 Выключено ламп и приборов: {count} шт.", show_alert=False)

        await asyncio.sleep(0.5)
        info = await get_user_info(token)
        if info:
            text, kb = build_all_devices_keyboard(info, page=page)
            try:
                await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        return

    # 9. Priority Device Toggles on Main Card
    if action == "sh_toggle_corridor":
        await callback.answer("🚪 Переключаю свет в коридоре...")
        ok, msg, _ = await toggle_device_by_name(token, "Свет коридор")
        if not ok:
            ok, msg = await execute_scenario(token, "Выключатель коридор")
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_toggle_bath":
        await callback.answer("🛁 Переключаю свет в ванной...")
        ok, msg, _ = await toggle_device_by_name(token, "Свет в ванной")
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_toggle_fan":
        await callback.answer("💨 Переключаю вытяжку...")
        ok, msg, _ = await toggle_device_by_name(token, "Вытяжка")
        if not ok:
            ok, msg = await execute_scenario(token, "Вытяжка в ванной")
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_toggle_floor":
        await callback.answer("♨️ Переключаю тёплый пол...")
        ok, msg, _ = await toggle_device_by_name(token, "Теплый пол")
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_scen_living":
        await callback.answer("🛋 Запускаю свет в гостиной...")
        ok, msg = await execute_scenario(token, "Свет в гостиной")
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_scen_bar":
        await callback.answer("🍸 Запускаю барную стойку...")
        ok, msg = await execute_scenario(token, "Барная стойка")
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_turn_off_all":
        await callback.answer("💡 Выключаю весь свет в доме...")
        ok, msg, count = await turn_off_all_lights(token)
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    if action == "sh_scenarios_list":
        info = await get_user_info(token)
        scenarios = info.get("scenarios", []) if info else []
        if not scenarios:
            await callback.answer("Сценарии не найдены.", show_alert=True)
            return

        kb_rows = []
        for sc in scenarios:
            kb_rows.append([InlineKeyboardButton(text=f"▶️ {sc['name']}", callback_data=f"sh_run_sc_{sc['id']}")])
        kb_rows.append([InlineKeyboardButton(text="🔙 Назад к панели", callback_data="sh_refresh")])

        await callback.message.edit_text(
            "🎬 <b>Доступные сценарии Яндекса:</b>\n\nНажмите на любой сценарий для его мгновенного запуска:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows)
        )
        return

    if action.startswith("sh_run_sc_"):
        sc_id = action.replace("sh_run_sc_", "")
        ok, msg = await execute_scenario(token, sc_id)
        await callback.answer(msg, show_alert=True)
        await _refresh_card_after_action(callback, token)
        return


async def _refresh_card_after_action(callback: types.CallbackQuery, token: str, alert_text: str = ""):
    if alert_text:
        try:
            clean_msg = alert_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
            await callback.answer(clean_msg, show_alert=False)
        except Exception:
            pass

    await asyncio.sleep(0.4)
    ok, report, meta = await build_smart_home_card(token)
    if ok:
        kb = get_smart_home_keyboard(meta.get("priority_states", {}))
        try:
            await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass
