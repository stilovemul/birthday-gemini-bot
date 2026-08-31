import re
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core.keyboards import get_main_menu
from core.gemini import ask_gemini
from modules.custom_rules.storage import (
    get_user_rules,
    add_custom_rule,
    toggle_rule_state,
    delete_custom_rule
)

logger = logging.getLogger("CustomRulesHandler")
router = Router(name="custom_rules")


def get_rules_keyboard(rules: list) -> InlineKeyboardMarkup:
    kb_rows = []
    for r in rules:
        st_icon = "🟢" if r.get("is_active", True) else "⚪️"
        btn_text = f"{st_icon} {r.get('title', 'Правило')[:24]}"
        kb_rows.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"rule_toggle_{r['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"rule_del_{r['id']}")
        ])

    kb_rows.append([
        InlineKeyboardButton(text="➕ Создать новое правило", callback_data="rule_add_prompt"),
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
        "<i>Нажимайте на тумблер 🟢/⚪️ для включения или выключения:</i>\n"
    ]

    if not rules:
        lines.append("<i>Список правил пуст. Нажмите «➕ Создать», чтобы добавить авто-триггер.</i>")
    else:
        for idx, r in enumerate(rules, 1):
            st = "🟢 Включено" if r.get("is_active", True) else "⚪️ Выключено"
            tt = r.get("trigger_type", "")
            h = f"{r.get('hour', 12):02d}:{r.get('minute', 0):02d}"

            if tt == "monthly_day":
                sched = f"Каждое {r.get('day_of_month', 1)}-е число в {h} MSK"
            elif tt == "weekly_day":
                days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
                d_str = ", ".join(days_map.get(d, "") for d in r.get("days_of_week", []))
                sched = f"Каждую неделю ({d_str}) в {h} MSK"
            else:
                sched = f"Ежедневно в {h} MSK"

            lines.append(f"{idx}. <b>{r.get('title')}</b> ({st})\n   ⏰ <i>{sched}</i>\n   💬 {r.get('action_text')}\n")

    lines.append("💡 <i>Чтобы создать правило, напишите фразу в свободной форме (например: «Каждую пятницу в 18:00 напоминай...»).</i>")
    return "\n".join(lines)


@router.message(Command("rules"))
@router.message(Command("automations"))
@router.message(F.text == "🧩 Мои правила")
async def cmd_custom_rules(message: types.Message):
    user_id = message.from_user.id
    rules = get_user_rules(user_id)
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(rules)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "rule_refresh")
async def cb_rule_refresh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rules = get_user_rules(user_id)
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(rules)
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("🔄 Обновлено!")


@router.callback_query(F.data.startswith("rule_toggle_"))
async def cb_rule_toggle(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rule_id = callback.data.replace("rule_toggle_", "")
    new_st = toggle_rule_state(user_id, rule_id)
    if new_st is not None:
        toast = "🟢 Правило включено!" if new_st else "⚪️ Правило выключено!"
        await callback.answer(toast, show_alert=False)
    else:
        await callback.answer("⚠️ Ошибка", show_alert=True)

    rules = get_user_rules(user_id)
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(rules)
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("rule_del_"))
async def cb_rule_del(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    rule_id = callback.data.replace("rule_del_", "")
    ok = delete_custom_rule(user_id, rule_id)
    if ok:
        await callback.answer("✅ Правило удалено!", show_alert=False)
    else:
        await callback.answer("⚠️ Не удалось удалить.", show_alert=True)

    rules = get_user_rules(user_id)
    text = format_rules_card(user_id)
    kb = get_rules_keyboard(rules)
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data == "rule_add_prompt")
async def cb_rule_add_prompt(callback: types.CallbackQuery):
    prompt_text = (
        "➕ <b>Как создать персональное правило:</b>\n\n"
        "Напишите фразу в свободной форме или надиктуйте голосом:\n\n"
        "👉 <code>Каждое 20-е число в 12:00 напоминай передать показания счетчиков</code>\n"
        "👉 <code>Каждую пятницу в 18:00 напоминай проверить уровень масла в авто</code>\n"
        "👉 <code>Каждое утро в 08:30 напоминай выпить стакан воды с лимоном</code>\n"
        "👉 <code>Каждый понедельник в 10:00 напоминай составить план на неделю</code>\n\n"
        "Нейросеть автоматически выделит расписание, день, время и текст напоминания!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад к правилам", callback_data="rule_refresh")]]
    )
    await callback.message.edit_text(prompt_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


# NLP Natural trigger for rule creation
@router.message(F.text.lower().startswith("создай правило") | F.text.lower().startswith("добавь правило") | F.text.lower().startswith("каждое ") | F.text.lower().startswith("каждый ") | F.text.lower().startswith("каждую "))
async def handle_rule_nlp(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    prompt = (
        f"Пользователь хочет создать периодическое автоматическое правило: '{text}'. "
        "Определи параметры правила: "
        "1. title: Короткий заголовок с эмодзи (до 30 символов). "
        "2. trigger_type: 'daily_time' (каждый день), 'monthly_day' (каждый месяц определенного числа), 'weekly_day' (каждую неделю в определенный день). "
        "3. day_of_month: число месяца от 1 до 31 (если monthly_day, иначе 0). "
        "4. days_of_week: массив чисел от 0 до 6, где 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт, 5=Сб, 6=Вс (если weekly_day). "
        "5. hour: час от 0 до 23 (по умолчанию 12). "
        "6. minute: минуты от 0 до 59 (по умолчанию 0). "
        "7. action_text: Текст сообщения, которое бот должен прислать. "
        "Верни ТОЛЬКО валидный JSON в формате: "
        '{"title": "💧 Показания счетчиков", "trigger_type": "monthly_day", "day_of_month": 20, "days_of_week": [], "hour": 12, "minute": 0, "action_text": "Пора передать показания счетчиков!"}'
    )
    ai_resp = await ask_gemini(user_id, prompt)
    try:
        import json
        m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            title = data.get("title", "Персональное правило")
            tt = data.get("trigger_type", "daily_time")
            dom = int(data.get("day_of_month", 0))
            dows = data.get("days_of_week", [])
            hour = int(data.get("hour", 12))
            minute = int(data.get("minute", 0))
            act_text = data.get("action_text", text)

            item = add_custom_rule(
                user_id=user_id,
                title=title,
                trigger_type=tt,
                action_text=act_text,
                hour=hour,
                minute=minute,
                day_of_month=dom,
                days_of_week=dows
            )

            h_str = f"{hour:02d}:{minute:02d} MSK"
            reply = (
                f"✅ <b>Персональное правило успешно создано и активно!</b>\n\n"
                f"📌 <b>{item['title']}</b>\n"
                f"⏰ <b>Время срабатывания:</b> в {h_str}\n"
                f"💬 <b>Действие:</b> {item['action_text']}\n\n"
                f"💡 <i>Бот будет автоматически присылать уведомление по этому расписанию.</i>"
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return
    except Exception as e:
        logger.warning(f"Error parsing rule NLP: {e}")

    await message.answer("⚠️ Не удалось разобрать параметры правила. Попробуйте так: <code>Каждое 20-е число в 12:00 напоминай передать показания</code>", parse_mode=ParseMode.HTML)
