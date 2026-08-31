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
from core.states import SubTrackerStates
from modules.subscription_tracker.storage import (
    reload_from_cloud,
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
                InlineKeyboardButton(text="➕ Добавить подписку / платёж", callback_data="sub_add_prompt"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data="sub_delete_menu")
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
        lines.append("<i>Список подписок пуст. Нажмите «➕ Добавить», чтобы внести сервис или платеж.</i>")
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
async def cmd_subscriptions(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    text = format_subscriptions_card(user_id)
    kb = get_subs_overview_keyboard()
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "sub_refresh")
async def cb_sub_refresh(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    reload_from_cloud()
    text = format_subscriptions_card(user_id)
    kb = get_subs_overview_keyboard()
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("🔄 Обновлено!")


@router.callback_query(F.data == "sub_cancel")
async def cb_sub_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    text = format_subscriptions_card(user_id)
    kb = get_subs_overview_keyboard()
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer("❌ Добавление отменено.")


@router.callback_query(F.data == "sub_add_prompt")
async def cb_sub_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SubTrackerStates.waiting_for_sub_text)
    prompt_text = (
        "💳 <b>Режим добавления регулярного платежа / подписки:</b>\n\n"
        "Напишите текст или надиктуйте голосом данные одного или сразу нескольких платежей:\n\n"
        "👉 <code>Ипотека 45000 рублей 20 числа</code>\n"
        "👉 <code>Кредит на авто 18000 рублей 5 числа</code>\n"
        "👉 <code>Яндекс Плюс 299 руб 15 числа</code>\n"
        "👉 <code>Аренда квартиры 38800 15 числа</code>\n\n"
        "💡 <i>В этом режиме любые слова (даже «ипотека» или «кредит») будут сохранены именно в раздел регулярных платежей и подписок!</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="sub_cancel")]
        ]
    )
    await callback.message.edit_text(prompt_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.message(SubTrackerStates.waiting_for_sub_text)
async def handle_sub_waiting_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text or ""

    if text.strip() in ["/cancel", "Отмена", "отмена", "❌ Отмена"]:
        await state.clear()
        card_text = format_subscriptions_card(user_id)
        await message.answer("❌ Добавление отменено.\n\n" + card_text, parse_mode=ParseMode.HTML, reply_markup=get_subs_overview_keyboard())
        return

    # Process input strictly as subscription(s)
    prompt = (
        f"Пользователь находится в разделе добавления регулярных платежей/подписок и прислал данные:\n'{text}'\n\n"
        "Твоя задача — извлечь ВСЕ платежи/подписки в массив объектов (даже если там ипотека, кредит, аренда или связь). "
        "Для каждого объекта определи: "
        "- name: понятное название (например: 'Ипотека', 'Яндекс Плюс', 'Ростелеком', 'Кредит на авто') "
        "- amount: сумма списания в рублях (число, например 45000, 299, 899) "
        "- payment_day: день месяца списания от 1 до 31 (число, например 15, 20, 1) "
        "- category: категория ('Финансы & Ипотека', 'Медиа & Музыка', 'Связь & Интернет', 'Дом & Аренда', 'Авто') "
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        '{"items": [{"name": "Ипотека", "amount": 45000, "payment_day": 20, "category": "Финансы & Ипотека"}]}'
    )
    ai_resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            items = data.get("items", [])
            if items and isinstance(items, list):
                added_items = []
                for it in items:
                    name = it.get("name", "Подписка")
                    amount = float(it.get("amount", 300))
                    day = int(it.get("payment_day", 1))
                    cat = it.get("category", "Платежи")
                    added = add_subscription(user_id, name, amount, day, category=cat)
                    added_items.append(added)

                await state.clear()
                reset_chat_session(user_id)
                stats = get_subscription_stats(user_id)

                lines = [
                    f"✅ <b>Успешно добавлено в раздел «Подписки и платежи» ({len(added_items)} шт.):</b>\n"
                ]
                for idx, it in enumerate(added_items, 1):
                    lines.append(f"{idx}. <b>{it['name']}</b> — <b>{it['amount']} ₽/мес</b> (<i>{it['payment_day']}-е число</i>, {it['category']})")

                lines.append(f"\n📊 <b>Всего расходов:</b> <b>{stats['monthly_total']} ₽/мес</b> (<b>{stats['yearly_total']} ₽/год</b>)")
                lines.append("🔔 <i>Бот предупредит за 2 дня и за 1 день до каждого списания!</i>")

                await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_subs_overview_keyboard())
                return
    except Exception as e:
        logger.warning(f"Error parsing sub in FSM state: {e}")

    await message.answer("⚠️ Не удалось разобрать параметры платежа. Попробуйте так: <code>Ипотека 45000 рублей 20 числа</code>", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "sub_delete_menu")
async def cb_sub_delete_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
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
async def cb_sub_del_item(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    sub_id = callback.data.replace("sub_del_", "")
    ok = delete_subscription(user_id, sub_id)
    reset_chat_session(user_id)
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
async def cb_sub_analytics(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
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
