import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu
from modules.smart_home.storage import get_user_smart_home_config, set_user_smart_home_token
from modules.smart_home.client import (
    build_smart_home_card,
    toggle_device_by_name,
    execute_scenario,
    turn_off_all_lights,
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
            InlineKeyboardButton(text="💡 Выключить весь свет ⚪️", callback_data="sh_turn_off_all"),
            InlineKeyboardButton(text="🔄 Обновить статус", callback_data="sh_refresh")
        ],
        [
            InlineKeyboardButton(text="🎬 Все сценарии", callback_data="sh_scenarios_list"),
            InlineKeyboardButton(text="📱 Комнаты и приборы", callback_data="sh_devices_list")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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

    # 1. Refresh Status
    if action == "sh_refresh":
        await callback.answer("🔄 Обновляю данные...")
        ok, report, meta = await build_smart_home_card(token)
        if ok:
            kb = get_smart_home_keyboard(meta.get("priority_states", {}))
            try:
                await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception:
                pass
        return

    # 2. Toggle Specific Priority Devices
    if action == "sh_toggle_corridor":
        await callback.answer("🚪 Переключаю свет в коридоре...")
        ok, msg, _ = await toggle_device_by_name(token, "Свет коридор")
        if not ok:
            # Fallback to scenario if switch isn't responding
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

    # 3. Scenarios
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

    # 4. Turn Off All Lights
    if action == "sh_turn_off_all":
        await callback.answer("💡 Выключаю весь свет в доме...")
        ok, msg, count = await turn_off_all_lights(token)
        await _refresh_card_after_action(callback, token, alert_text=msg)
        return

    # 5. List Scenarios
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

    # 6. Run Individual Scenario
    if action.startswith("sh_run_sc_"):
        sc_id = action.replace("sh_run_sc_", "")
        ok, msg = await execute_scenario(token, sc_id)
        await callback.answer(msg, show_alert=True)
        await _refresh_card_after_action(callback, token)
        return

    # 7. List Rooms and Devices
    if action == "sh_devices_list":
        info = await get_user_info(token)
        if not info:
            await callback.answer("Ошибка загрузки.", show_alert=True)
            return

        rooms = {r["id"]: r["name"] for r in info.get("rooms", [])}
        devices = info.get("devices", [])

        lines = ["📱 <b>Устройства по комнатам:</b>\n"]
        for r_id, r_name in rooms.items():
            r_devs = [d for d in devices if d.get("room") == r_id]
            if not r_devs:
                continue
            lines.append(f"🏠 <b>{r_name}:</b>")
            for d in r_devs:
                st_icon = ""
                for cap in d.get("capabilities", []) or []:
                    if cap.get("type") == "devices.capabilities.on_off":
                        c_val = (cap.get("state") or {}).get("value")
                        st_icon = " 🟢" if c_val else " ⚪️"
                lines.append(f"  • {d.get('name')}{st_icon}")
            lines.append("")

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад к панели", callback_data="sh_refresh")]])
        await callback.message.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
        return


async def _refresh_card_after_action(callback: types.CallbackQuery, token: str, alert_text: str = ""):
    if alert_text:
        try:
            # Clean HTML tags for toast answer
            clean_msg = alert_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
            await callback.answer(clean_msg, show_alert=False)
        except Exception:
            pass

    # Wait 0.5s for Yandex to apply state then re-render card
    import asyncio
    await asyncio.sleep(0.5)
    ok, report, meta = await build_smart_home_card(token)
    if ok:
        kb = get_smart_home_keyboard(meta.get("priority_states", {}))
        try:
            await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass
