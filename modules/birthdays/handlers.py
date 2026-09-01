import re
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import BirthdayStates
from core.gemini import ask_gemini, reset_chat_session
from modules.birthdays.storage import (
    load_birthdays,
    add_birthday,
    delete_birthday,
    get_sorted_birthdays,
    format_date_entry,
    format_age_word,
    parse_date_string
)
from modules.birthdays.sync import pull_birthdays_from_github, push_birthdays_to_github

logger = logging.getLogger("BirthdayHandlers")
router = Router(name="birthdays")


def get_birthdays_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить день рождения", callback_data="bday_add_prompt"),
                InlineKeyboardButton(text="🗑 Удалить запись", callback_data="bday_delete_menu")
            ],
            [
                InlineKeyboardButton(text="🔍 Найти день рождения", callback_data="bday_search_prompt"),
                InlineKeyboardButton(text="🔄 Обновить список", callback_data="bday_refresh")
            ]
        ]
    )


def format_birthdays_card() -> str:
    items = get_sorted_birthdays()
    if not items:
        return (
            "🎂 <b>Календарь дней рождения:</b>\n\n"
            "📭 <i>Список пуст. Нажмите «➕ Добавить день рождения», чтобы сохранить даты близких.</i>"
        )

    lines = [
        f"🎂 <b>Все сохраненные дни рождения ({len(items)} чел.):</b>\n"
    ]

    upcoming_count = sum(1 for b in items if b["days_left"] <= 30)

    for idx, item in enumerate(items, 1):
        name = item["name"]
        date_str = format_date_entry(item)
        days_left = item["days_left"]
        note = item.get("note", "").strip()

        age_info = f" ({format_age_word(item['turning_age'])})" if item.get("turning_age") else ""
        if days_left == 0:
            left_badge = "🔥 <b>СЕГОДНЯ!</b>"
        elif days_left == 1:
            left_badge = "⏳ <b>ЗАВТРА!</b>"
        elif days_left <= 14:
            left_badge = f"⚡️ <b>через {days_left} дн.</b>"
        else:
            left_badge = f"через {days_left} дн."

        note_str = f" • <i>{note}</i>" if note else ""
        lines.append(f"{idx}. <b>{name}</b> — {date_str}{age_info}\n   └ 🗓 {left_badge}{note_str} <code>[id:{item['id']}]</code>")

    lines.append(f"\n💡 <i>Ближайших в этом месяце: <b>{upcoming_count}</b>. Бот напомнит заранее в 09:00 MSK!</i>")
    return "\n".join(lines)


@router.message(Command("birthdays"))
@router.message(Command("bday"))
@router.message(Command("list"))
@router.message(F.text.in_([
    "🎂 Дни рождения", "🎂 Дни Рождения", "📋 Все дни рождения",
    "📋 Список всех ДР", "📋 Список всех дней рождения", "📋 Все ДР"
]))
async def cmd_birthdays_overview(message: types.Message, state: FSMContext):
    await state.clear()
    pull_birthdays_from_github()
    text = format_birthdays_card()
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_birthdays_keyboard())


@router.callback_query(F.data == "bday_refresh")
async def cb_bday_refresh(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    pull_birthdays_from_github()
    text = format_birthdays_card()
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_birthdays_keyboard())
    except Exception:
        pass
    await callback.answer("🔄 Список обновлен из облака!")


@router.callback_query(F.data == "bday_add_prompt")
async def cb_bday_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BirthdayStates.waiting_for_birthday_text)
    prompt_text = (
        "🎂 <b>Режим добавления дней рождения:</b>\n\n"
        "Напишите текст или надиктуйте голосом одно или сразу несколько имен с датами:\n\n"
        "👉 <code>Мама 06.04.1964</code>\n"
        "👉 <code>Саша Ломанова 15 сентября</code>\n"
        "👉 <code>Иван 12.08.1990 любит кофе</code>\n\n"
        "💡 <i>В этом режиме любые имена и даты будут сохранены в базу дней рождения!</i>"
    )
    await callback.message.answer(prompt_text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Дни рождения"))
    await callback.answer()


@router.message(BirthdayStates.waiting_for_birthday_text)
async def handle_birthday_waiting_input(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        card_text = format_birthdays_card()
        await message.answer("🏁 <b>Режим добавления ДР завершен.</b>\n\n" + card_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    # NLP parser for single or batch birthdays
    prompt = (
        f"Пользователь находится в режиме добавления дней рождения и прислал данные:\n'{text}'\n\n"
        "Твоя задача — извлечь ВСЕ имена и даты в массив объектов. "
        "Для каждого объекта определи: "
        "- name: имя и фамилия (например: 'Мама', 'Саша Ломанова', 'Кирилл Коротков') "
        "- day: день месяца (число 1-31) "
        "- month: месяц (число 1-12) "
        "- year: год рождения (число например 1995 или null если не указан) "
        "- note: примечание/подарок если есть "
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        '{"items": [{"name": "Саша Ломанова", "day": 15, "month": 9, "year": 1995, "note": ""}]}'
    )
    ai_resp = await ask_gemini(user_id, prompt)
    try:
        import json
        m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            items = data.get("items", [])
            if items and isinstance(items, list):
                added_msgs = []
                for it in items:
                    name = it.get("name", "").strip()
                    d = it.get("day")
                    m_num = it.get("month")
                    y = it.get("year")
                    nt = it.get("note", "")
                    if name and d and m_num:
                        d_str = f"{d}.{m_num}.{y}" if y else f"{d}.{m_num}"
                        success, reply_msg, _ = add_birthday(name, d_str, nt)
                        if success:
                            added_msgs.append(f"• <b>{name}</b> ({d_str})")

                if added_msgs:
                    await state.clear()
                    reset_chat_session(user_id)
                    res_text = (
                        f"✅ <b>Успешно сохранено в базу ({len(added_msgs)}):</b>\n" +
                        "\n".join(added_msgs) +
                        "\n\n☁️ <i>Синхронизировано с GitHub облаком!</i>\n\n" +
                        format_birthdays_card()
                    )
                    await message.answer(res_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                    return
    except Exception as e:
        logger.warning(f"Error parsing birthday FSM: {e}")

    await message.answer("⚠️ Не удалось распознать дату. Попробуйте в формате: <code>Имя 15.09.1995</code> или <code>Имя 15 сентября</code>", parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "bday_delete_menu")
async def cb_bday_delete_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    items = get_sorted_birthdays()
    if not items:
        await callback.answer("Список пуст.", show_alert=True)
        return

    kb_rows = []
    for b in items:
        btn_text = f"❌ {b['name']} ({b['day']}.{b['month']})"
        kb_rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"bday_del_{b['id']}")])
    kb_rows.append([InlineKeyboardButton(text="🔙 Назад к списку", callback_data="bday_refresh")])

    await callback.message.edit_text(
        "🗑 <b>Выберите запись для удаления:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bday_del_"))
async def cb_bday_del_item(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    b_id = callback.data.replace("bday_del_", "")
    success, reply_msg = delete_birthday(b_id)
    reset_chat_session(callback.from_user.id)
    if success:
        await callback.answer("✅ Запись удалена!", show_alert=False)
    else:
        await callback.answer("⚠️ Не удалось удалить.", show_alert=True)

    text = format_birthdays_card()
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_birthdays_keyboard())
    except Exception:
        pass


@router.callback_query(F.data == "bday_search_prompt")
async def cb_bday_search_prompt(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔍 <b>Поиск дня рождения:</b>\n"
        "Напишите в чат имя: <code>/when Мама</code> или просто спросите: <i>«Когда день рождения у Папы?»</i>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()
