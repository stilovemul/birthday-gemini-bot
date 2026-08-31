import re
import json
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core.keyboards import get_main_menu
from core.gemini import ask_gemini, reset_chat_session
from modules.custom_rules.storage import (
    reload_from_cloud,
    get_user_rules,
    add_custom_rule,
    toggle_rule_state,
    mark_rule_completed,
    delete_custom_rule
)

logger = logging.getLogger("CustomRulesHandler")
router = Router(name="custom_rules")


def get_rules_keyboard(rules: list) -> InlineKeyboardMarkup:
    kb_rows = []
    for r in rules:
        # Green icon if completed for current period, White if pending
        is_done = r.get("is_completed_now", False)
        done_icon = "🟢" if is_done else "⚪️"
        btn_done_text = f"{done_icon} {r.get('title', 'Правило')[:22]}"
        
        # Row with completion toggle and delete
        kb_rows.append([
            InlineKeyboardButton(text=btn_done_text, callback_data=f"rule_done_{r['id']}"),
            InlineKeyboardButton(text="⚙️ Вкл/Выкл", callback_data=f"rule_toggle_{r['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"rule_del_{r['id']}")
        ])

    kb_rows.append([
        InlineKeyboardButton(text="➕ Создать правило", callback_data="rule_add_prompt"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="rule_refresh")
    ])
    kb_rows.append([
        InlineKeyboardButton(text="📱 Открыть Mini App Дашборд", web_app=WebAppInfo(url="https://birthday-gemini-bot.onrender.com/app"))
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb_rows)


def format_rules_card(user_id: int) -> str:
    rules = get_user_rules(user_id)
    lines = [
        "🧩 <b>Конструктор персональных правил («Если... то...»):</b>\n",
        f"⚡ Всего правил в базе: <b>{len(rules)} шт.</b>",
        "<i>Нажимайте на кнопку ⚪️, чтобы отметить выполненным 🟢 на текущий период:</i>\n"
    ]

    if not rules:
        lines.append("<i>Список правил пуст. Напишите, например: «Передать показания с 20 по 24 число каждого месяца»</i>")
    else:
        for idx, r in enumerate(rules, 1):
            is_done = r.get("is_completed_now", False)
            st_done = "🟢 <b>Выполнено на этот период</b>" if is_done else "⚪️ <b>Ожидает выполнения</b>"
            is_active = " (Активно)" if r.get("is_active", True) else " <i>(Выключено)</i>"
            
            tt = r.get("trigger_type", "")
            h = f"{r.get('hour', 12):02d}:{r.get('minute', 0):02d}"

            if tt == "monthly_range":
                sched = f"Каждый месяц с {r.get('start_day')} по {r.get('end_day')} число в {h} MSK"
            elif tt == "monthly_day":
                sched = f"Каждое {r.get('day_of_month', 1)}-е число в {h} MSK"
            elif tt == "weekly_day":
                days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
                d_str = ", ".join(days_map.get(d, "") for d in r.get("days_of_week", []))
                sched = f"Каждую неделю ({d_str}) в {h} MSK"
            else:
                sched = f"Ежедневно в {h} MSK"

            lines.append(
                f"{idx}. <b>{r.get('title')}</b>{is_active}\n"
                f"   🗓 <i>{sched}</i>\n"
                f"   💬 {r.get('action_text')}\n"
                f"   👉 Статус: {st_done}\n"
            )

    lines.append("💡 <i>Бот будет напоминать каждый день в указанный период, пока вы не отметите зеленый значок 🟢!</i>")
    return "\n".join(lines)


@router.message(Command("rules"))
@router.message(Command("automations"))
@router.message(F.text == "🧩 Мои правила")
async def cmd_custom_rules(message: types.Message):
    user_id = message.from_user.id
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "rule_refresh")
async def cb_rule_refresh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    reload_from_cloud()
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("🔄 Обновлено!")


@router.callback_query(F.data.startswith("rule_done_"))
async def cb_rule_done(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rule_id = callback.data.replace("rule_done_", "")
    is_done = mark_rule_completed(user_id, rule_id)
    reset_chat_session(user_id)

    if is_done:
        await callback.answer("🟢 Отлично! Задача отмечена выполненной на этот период!", show_alert=True)
    else:
        await callback.answer("⚪️ Статус сброшен: задача снова ожидает выполнения.", show_alert=False)

    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("rule_toggle_"))
async def cb_rule_toggle(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rule_id = callback.data.replace("rule_toggle_", "")
    new_st = toggle_rule_state(user_id, rule_id)
    reset_chat_session(user_id)
    if new_st is not None:
        toast = "🟢 Правило включено!" if new_st else "⚪️ Правило выключено!"
        await callback.answer(toast, show_alert=False)
    else:
        await callback.answer("⚠️ Ошибка", show_alert=True)

    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("rule_del_"))
async def cb_rule_del(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rule_id = callback.data.replace("rule_del_", "")
    ok = delete_custom_rule(user_id, rule_id)
    reset_chat_session(user_id)
    if ok:
        await callback.answer("✅ Правило удалено!", show_alert=False)
    else:
        await callback.answer("⚠️ Не удалось удалить.", show_alert=True)

    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data == "rule_add_prompt")
async def cb_rule_add_prompt(callback: types.CallbackQuery):
    prompt_text = (
        "➕ <b>Как создать персональное правило:</b>\n\n"
        "Напишите фразу в свободной форме или надиктуйте голосом:\n\n"
        "👉 <code>Передать показания счетчиков каждый месяц с 20 по 24 число</code>\n"
        "👉 <code>Каждую пятницу в 18:00 напоминай проверить уровень масла в авто</code>\n"
        "👉 <code>Каждое утро в 08:30 напоминай выпить стакан воды с лимоном</code>\n"
        "👉 <code>Каждый месяц 1 числа оплатить аренду квартиры</code>\n\n"
        "Нейросеть автоматически выделит диапазон дней, время и текст напоминания!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад к правилам", callback_data="rule_refresh")]]
    )
    await callback.message.edit_text(prompt_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()
