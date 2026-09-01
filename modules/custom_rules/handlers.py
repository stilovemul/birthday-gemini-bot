import re
import json
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core.keyboards import get_main_menu
from core.gemini import ask_gemini, reset_chat_session
from core.states import CustomRuleStates
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
        is_done = r.get("is_completed_now", False)
        done_icon = "🟢" if is_done else "⚪️"
        btn_done_text = f"{done_icon} {r.get('title', 'Правило')[:22]}"
        
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
        lines.append("<i>Список правил пуст. Нажмите «➕ Создать правило», чтобы добавить автоматизацию.</i>")
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
@router.message(F.text.in_(["🧩 Правила", "🧩 Мои правила", "Правила", "Мои правила"]))
async def cmd_custom_rules(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "rule_refresh")
async def cb_rule_refresh(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    reload_from_cloud()
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("🔄 Обновлено!")


@router.callback_query(F.data == "rule_cancel")
async def cb_rule_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(get_user_rules(user_id))
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("❌ Создание правила отменено.")


@router.callback_query(F.data == "rule_add_prompt")
async def cb_rule_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(CustomRuleStates.waiting_for_rule_text)
    prompt_text = (
        "🧩 <b>Режим создания персонального правила:</b>\n\n"
        "Напишите текст или надиктуйте периодическую задачу голосом:\n\n"
        "👉 <code>Передать показания счётчиков каждый месяц с 20 по 24 число</code>\n"
        "👉 <code>Каждую пятницу в 18:00 напоминай проверить уровень масла в авто</code>\n"
        "👉 <code>Каждое утро в 08:30 напоминай выпить витамины</code>\n"
        "👉 <code>Каждый месяц 1 числа оплатить аренду квартиры</code>\n\n"
        "💡 <i>В этом режиме любой ввод будет сохранен именно в раздел «Мои правила»!</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="rule_cancel")]
        ]
    )
    await callback.message.edit_text(prompt_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.message(CustomRuleStates.waiting_for_rule_text)
async def handle_rule_waiting_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text or ""

    if text.strip() in ["/cancel", "Отмена", "отмена", "❌ Отмена"]:
        await state.clear()
        card_text = format_rules_card(user_id)
        await message.answer("❌ Создание отменено.\n\n" + card_text, parse_mode=ParseMode.HTML, reply_markup=get_rules_keyboard(get_user_rules(user_id)))
        return

    # Process strictly as custom rule
    prompt = (
        f"Пользователь находится в режиме создания персонального правила/повторяющейся задачи и написал:\n'{text}'\n\n"
        "Определи параметры правила: "
        "1. title: Короткий заголовок с понятным эмодзи (до 30 символов, например '💧 Передать показания счетчиков'). "
        "2. trigger_type: "
        "   - 'monthly_range' (если указан диапазон дат каждого месяца, например 'с 20 по 24 число') "
        "   - 'monthly_day' (если точный день месяца, например '20-е число') "
        "   - 'weekly_day' (если определенный день недели, например 'каждую пятницу') "
        "   - 'daily_time' (если каждый день) "
        "3. start_day: начальное число диапазона от 1 до 31 (число, например 20, если monthly_range, иначе 0). "
        "4. end_day: конечное число диапазона от 1 до 31 (число, например 24, если monthly_range, иначе 0). "
        "5. day_of_month: число месяца (если monthly_day или start_day). "
        "6. days_of_week: массив чисел от 0 до 6, где 0=Пн, 4=Пт, 6=Вс (если weekly_day). "
        "7. hour: час напоминания от 0 до 23 (по умолчанию 12). "
        "8. minute: минуты от 0 до 59 (по умолчанию 0). "
        "9. action_text: Понятный текст напоминания / инструкции. "
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        '{"title": "💧 Передать показания счетчиков", "trigger_type": "monthly_range", "start_day": 20, "end_day": 24, "day_of_month": 20, "days_of_week": [], "hour": 12, "minute": 0, "action_text": "Пора передать показания счетчиков воды и света!"}'
    )
    ai_resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            item = add_custom_rule(
                user_id=user_id,
                title=data.get("title", "Персональное правило"),
                trigger_type=data.get("trigger_type", "daily_time"),
                action_text=data.get("action_text", text),
                hour=int(data.get("hour", 12)),
                minute=int(data.get("minute", 0)),
                start_day=int(data.get("start_day", 0)),
                end_day=int(data.get("end_day", 0)),
                day_of_month=int(data.get("day_of_month", 0)),
                days_of_week=data.get("days_of_week", [])
            )
            await state.clear()
            reset_chat_session(user_id)

            h_str = f"{item['hour']:02d}:{item['minute']:02d} MSK"
            tt = item.get("trigger_type")
            if tt == "monthly_range":
                sched_desc = f"каждый месяц с {item.get('start_day')} по {item.get('end_day')} число"
            elif tt == "monthly_day":
                sched_desc = f"каждое {item.get('day_of_month')}-е число"
            elif tt == "weekly_day":
                sched_desc = "еженедельно"
            else:
                sched_desc = "ежедневно"

            reply = (
                f"✅ <b>Персональное правило создано и добавлено в базу:</b>\n\n"
                f"📌 <b>{item['title']}</b>\n"
                f"🗓 <b>Период:</b> {sched_desc} (в {h_str})\n"
                f"💬 <b>Действие:</b> {item['action_text']}\n"
                f"👉 <b>Статус:</b> ⚪️ <i>Ожидает выполнения</i>\n\n"
                f"🔔 <i>Бот будет присылать напоминание, пока вы не нажмете зеленую кнопку 🟢 [Выполнено]!</i>"
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_rules_keyboard(get_user_rules(user_id)))
            return
    except Exception as e:
        logger.warning(f"Error parsing rule in FSM state: {e}")

    await message.answer("⚠️ Не удалось разобрать параметры правила. Попробуйте так: <code>Передать показания с 20 по 24 число</code>", parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("rule_done_"))
async def cb_rule_done(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
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
async def cb_rule_toggle(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
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
async def cb_rule_del(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
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
