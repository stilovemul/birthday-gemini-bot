import re
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core.keyboards import get_main_menu
from core.gemini import ask_gemini
from modules.subscription_tracker.storage import (
    get_user_subscriptions,
    add_subscription,
    delete_subscription,
    get_subscription_stats
)

logger = logging.getLogger("SubscriptionHandler")
router = Router(name="subscription_tracker")


def get_subs_overview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить подписку", callback_data="sub_add_prompt"),
                InlineKeyboardButton(text="🗑 Удалить подписку", callback_data="sub_delete_menu")
            ],
            [
                InlineKeyboardButton(text="📊 Аналитика по категориям", callback_data="sub_analytics"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="sub_refresh")
            ],
            [
                InlineKeyboardButton(text="📱 Открыть Mini App Дашборд", web_app=WebAppInfo(url="https://birthday-gemini-bot.onrender.com/app"))
            ]
        ]
    )


def format_subscriptions_card(user_id: int) -> str:
    stats = get_subscription_stats(user_id)
    items = stats["items"]
    m_tot = stats["monthly_total"]
    y_tot = stats["yearly_total"]

    lines = [
        "💳 <b>Трекер регулярных подписок и платежей:</b>\n",
        f"📊 Всего сервисов: <b>{len(items)} шт.</b>",
        f"💰 Расход в месяц: <b>{m_tot} ₽</b> | В год: <b>{y_tot} ₽</b>\n",
        "📋 <b>Ближайшие списания:</b>"
    ]

    if not items:
        lines.append("<i>Список подписок пуст. Нажмите «➕ Добавить», чтобы внести сервис.</i>")
    else:
        for s in items:
            days = s.get("days_left", 0)
            if days == 0:
                d_str = "🔥 <b>СЕГОДНЯ!</b>"
            elif days == 1:
                d_str = "⏳ <b>Завтра</b>"
            elif days <= 3:
                d_str = f"⚠️ через {days} дн."
            else:
                d_str = f"через {days} дн."

            amt = s.get("amount", 0)
            name = s.get("name", "Подписка")
            cat = s.get("category", "")
            np_str = s.get("next_payment_date", "")

            lines.append(f"• <b>{name}</b> — <b>{amt} ₽</b> ({cat})\n  🗓 Списание: <i>{np_str}</i> ({d_str})")

    lines.append("\n💡 <i>Бот автоматически предупредит за 2 дня и за 1 день до каждого списания!</i>")
    return "\n".join(lines)


@router.message(Command("subs"))
@router.message(Command("subscriptions"))
@router.message(F.text == "💳 Подписки")
async def cmd_subscriptions(message: types.Message):
    user_id = message.from_user.id
    text = format_subscriptions_card(user_id)
    kb = get_subs_overview_keyboard()
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "sub_refresh")
async def cb_sub_refresh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text = format_subscriptions_card(user_id)
    kb = get_subs_overview_keyboard()
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("🔄 Обновлено!")


@router.callback_query(F.data == "sub_add_prompt")
async def cb_sub_add_prompt(callback: types.CallbackQuery):
    prompt_text = (
        "➕ <b>Как быстро добавить подписку:</b>\n\n"
        "Просто напишите в чат текстом или надиктуйте голосом:\n\n"
        "👉 <code>Подписка Яндекс Плюс 299 руб 15 числа</code>\n"
        "👉 <code>Добавь подписку Домашний интернет 550р 1 числа</code>\n"
        "👉 <code>Подписка Телеграм Премиум 300 25 числа Связь</code>\n\n"
        "Бот поймет название, сумму, день списания и сразу сохранит!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад к списку", callback_data="sub_refresh")]]
    )
    await callback.message.edit_text(prompt_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "sub_delete_menu")
async def cb_sub_delete_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    subs = get_user_subscriptions(user_id)
    if not subs:
        await callback.answer("Список пуст.", show_alert=True)
        return

    kb_rows = []
    for s in subs:
        btn_text = f"❌ {s['name']} ({s['amount']} ₽)"
        kb_rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"sub_del_{s['id']}")])
    kb_rows.append([InlineKeyboardButton(text="🔙 Назад к списку", callback_data="sub_refresh")])

    await callback.message.edit_text(
        "🗑 <b>Выберите подписку для удаления:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub_del_"))
async def cb_sub_del_item(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sub_id = callback.data.replace("sub_del_", "")
    ok = delete_subscription(user_id, sub_id)
    if ok:
        await callback.answer("✅ Подписка успешно удалена!", show_alert=False)
    else:
        await callback.answer("⚠️ Не удалось удалить подписку.", show_alert=True)

    text = format_subscriptions_card(user_id)
    kb = get_subs_overview_keyboard()
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data == "sub_analytics")
async def cb_sub_analytics(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    stats = get_subscription_stats(user_id)
    cats = stats["categories"]
    m_tot = stats["monthly_total"]
    y_tot = stats["yearly_total"]

    lines = [
        "📊 <b>Аналитика расходов на подписки:</b>\n",
        f"💳 Всего сервисов: <b>{stats['total_count']} шт.</b>",
        f"📅 В месяц: <b>{m_tot} ₽</b>",
        f"📆 В год: <b>{y_tot} ₽</b>\n",
        "📂 <b>Распределение по категориям:</b>"
    ]

    for cat, val in sorted(cats.items(), key=lambda x: -x[1]):
        pct = round((val / m_tot) * 100) if m_tot > 0 else 0
        lines.append(f"• <b>{cat}</b>: {val} ₽/мес ({pct}%)")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад к подпискам", callback_data="sub_refresh")]]
    )
    await callback.message.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


# Natural text parser for adding subscription
@router.message(F.text.lower().startswith("подписка") | F.text.lower().startswith("добавь подписку") | F.text.lower().startswith("запиши подписку"))
async def handle_sub_nlp(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    prompt = (
        f"Пользователь хочет добавить регулярную подписку: '{text}'. "
        "Извлеки название сервиса, сумму в рублях, число месяца (день списания от 1 до 31) и категорию. "
        "Верни ТОЛЬКО валидный JSON в формате: "
        '{"name": "Яндекс Плюс", "amount": 299, "payment_day": 15, "category": "Медиа"}'
    )
    ai_resp = await ask_gemini(user_id, prompt)
    try:
        import json
        m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            name = data.get("name", "Подписка")
            amount = float(data.get("amount", 300))
            day = int(data.get("payment_day", 1))
            cat = data.get("category", "Сервисы")

            item = add_subscription(user_id, name, amount, day, category=cat)
            reply = (
                f"✅ <b>Подписка успешно сохранена!</b>\n\n"
                f"• Сервис: <b>{item['name']}</b>\n"
                f"• Сумма: <b>{item['amount']} ₽/мес</b>\n"
                f"• День списания: <b>{item['payment_day']}-е число</b> (следующее: <i>{item['next_payment_date']}</i>)\n"
                f"• Категория: <i>{item['category']}</i>\n\n"
                f"🔔 Бот напомнит вам за 2 дня и за 1 день до списания!"
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return
    except Exception as e:
        logger.warning(f"Error parsing sub NLP: {e}")

    await message.answer("⚠️ Не удалось разобрать параметры подписки. Попробуйте так: <code>Подписка Название 300 руб 15 числа</code>", parse_mode=ParseMode.HTML)
