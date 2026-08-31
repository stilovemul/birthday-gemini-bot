import re
from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from core.keyboards import get_main_menu, get_birthday_submenu
from modules.birthdays.storage import (
    load_birthdays,
    add_birthday,
    delete_birthday,
    get_sorted_birthdays,
    format_date_entry,
    format_age_word,
    parse_date_string
)
from modules.birthdays.notifier import check_and_notify

router = Router(name="birthdays")


def parse_add_arguments(text: str):
    cleaned = re.sub(r"^/add\s+", "", text.strip(), flags=re.IGNORECASE).strip()
    if not cleaned:
        return None

    patterns = [
        r"(\d{1,2}[./\-]\d{1,2}(?:[./\-]\d{2,4})?)",
        r"(\d{4}-\d{1,2}-\d{1,2})",
        r"(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)(?:\s+\d{2,4})?)"
    ]

    for pat in patterns:
        m = re.search(pat, cleaned, re.IGNORECASE)
        if m:
            date_part = m.group(1)
            start, end = m.span()
            name_part = cleaned[:start].strip()
            note_part = cleaned[end:].strip()

            if not name_part:
                rest = cleaned[end:].strip().split(maxsplit=1)
                if rest:
                    name_part = rest[0]
                    note_part = rest[1] if len(rest) > 1 else ""

            if name_part and parse_date_string(date_part):
                return name_part, date_part, note_part

    return None


def search_birthday_by_query(query: str):
    q = query.lower().strip()
    # Normalize common words
    q = re.sub(r"^(?:когда|какого\s+числа|узнай|посмотри|день\s+рождения|др|у)\s*", "", q).strip()
    q = re.sub(r"[?!.,]", "", q).strip()
    
    items = get_sorted_birthdays()
    # 1. Exact or partial substring match
    for item in items:
        name = item["name"].lower()
        if q in name or name in q:
            return item
        # check mama / mamy / pape
        if ("мам" in q and "мам" in name) or ("пап" in q and "пап" in name) or ("жен" in q and "жен" in name) or ("брат" in q and "брат" in name):
            return item
    return None


@router.message(F.text == "🎂 Дни рождения")
async def cmd_birthday_menu(message: types.Message):
    await message.answer("🎂 <b>Раздел: Дни рождения</b>\nВыберите действие в меню ниже 👇", parse_mode=ParseMode.HTML, reply_markup=get_birthday_submenu())


@router.message(F.text == "🔙 Главное меню")
async def cmd_back_main(message: types.Message):
    await message.answer("🏠 Главное меню:", reply_markup=get_main_menu())


@router.message(Command("when"))
@router.message(Command("bday"))
async def cmd_when_birthday(message: types.Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🔍 Укажите имя: <code>/when Мама</code> или <code>/when Папа</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    query = parts[1].strip()
    target = search_birthday_by_query(query)
    if target:
        date_str = format_date_entry(target)
        days_left = target["days_left"]
        age_str = f" (исполняется <b>{format_age_word(target['turning_age'])}</b>)" if target.get("turning_age") else ""
        left_str = "🔥 <b>СЕГОДНЯ!</b>" if days_left == 0 else (f"⏳ <b>Завтра!</b>" if days_left == 1 else f"через <b>{days_left} дн.</b>")
        note_str = f"\n🎁 <i>Заметка: {target['note']}</i>" if target.get("note") else ""

        text = (
            f"🎂 <b>День рождения: {target['name']}</b>\n\n"
            f"🗓 <b>Дата:</b> {date_str}{age_str}\n"
            f"⏳ <b>Осталось:</b> {left_str}{note_str}"
        )
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
    else:
        await message.answer(f"🔍 В базе пока нет дня рождения для «{query}». Добавить: <code>/add {query} ДД.ММ.ГГГГ</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(F.text.regexp(r"(?i)^(?:когда|какого\s+числа)\s+(?:день\s+рождения|др)\s+(?:у\s+)?(.+)"))
async def handle_natural_when_birthday(message: types.Message):
    match = re.search(r"(?i)^(?:когда|какого\s+числа)\s+(?:день\s+рождения|др)\s+(?:у\s+)?(.+)", message.text)
    if match:
        query = match.group(1).strip()
        target = search_birthday_by_query(query)
        if target:
            date_str = format_date_entry(target)
            days_left = target["days_left"]
            age_str = f" (исполнится <b>{format_age_word(target['turning_age'])}</b>)" if target.get("turning_age") else ""
            left_str = "🔥 <b>СЕГОДНЯ!</b>" if days_left == 0 else (f"⏳ <b>Завтра!</b>" if days_left == 1 else f"через <b>{days_left} дн.</b>")
            note_str = f"\n🎁 <i>Заметка: {target['note']}</i>" if target.get("note") else ""

            text = (
                f"🎂 <b>День рождения: {target['name']}</b>\n\n"
                f"🗓 <b>Дата:</b> {date_str}{age_str}\n"
                f"⏳ <b>Осталось:</b> {left_str}{note_str}"
            )
            await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    # If not found, let Gemini AI answer with context
    pass


@router.message(Command("add"))
async def cmd_add(message: types.Message):
    text = message.text or ""
    parsed = parse_add_arguments(text)
    if not parsed:
        await message.answer(
            "❌ Не удалось распознать запись.\nФормат: <code>/add Имя ДД.ММ.ГГГГ [Заметка]</code>\nПример: <code>/add Мама 06.04.1964 Цветы</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    name, date_str, note = parsed
    success, reply_msg, _ = add_birthday(name, date_str, note)
    await message.answer(reply_msg, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("del"))
async def cmd_del(message: types.Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите имя или ID для удаления: <code>/del Иван</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    identifier = parts[1].strip()
    success, reply_msg = delete_birthday(identifier)
    await message.answer(reply_msg, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("list"))
@router.message(F.text == "📋 Все дни рождения")
async def cmd_list(message: types.Message):
    items = get_sorted_birthdays()
    if not items:
        await message.answer("📭 Список дней рождения пока пуст.\nДобавьте: <code>/add Имя ДД.ММ.ГГГГ</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    lines = [f"📋 <b>Список всех дней рождения ({len(items)}):</b>\n"]
    for idx, item in enumerate(items, 1):
        name = item["name"]
        date_str = format_date_entry(item)
        days_left = item["days_left"]
        item_id = item["id"]
        note = item.get("note", "").strip()

        age_info = f" ({format_age_word(item['turning_age'])})" if item.get("turning_age") else ""
        left_badge = "🔥 <b>СЕГОДНЯ!</b>" if days_left == 0 else (f"⏳ <b>Завтра</b>" if days_left == 1 else f"через {days_left} дн.")
        note_str = f"\n   └ 🎁 <i>{note}</i>" if note else ""
        lines.append(f"{idx}. <b>{name}</b> — {date_str}{age_info}\n   └ 🗓 {left_badge} <code>[id:{item_id}]</code>{note_str}")

    await message.answer("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("upcoming"))
@router.message(F.text == "📅 Ближайшие ДР")
async def cmd_upcoming(message: types.Message):
    items = get_sorted_birthdays()
    upcoming = [b for b in items if b["days_left"] <= 30]

    if not upcoming:
        await message.answer("🌴 В ближайшие 30 дней дней рождения нет.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    lines = [f"📅 <b>Ближайшие дни рождения на 30 дней ({len(upcoming)}):</b>\n"]
    for idx, item in enumerate(upcoming, 1):
        name = item["name"]
        next_dt = item["next_date"].strftime("%d.%m")
        days_left = item["days_left"]
        note = item.get("note", "").strip()
        age_info = f" ({format_age_word(item['turning_age'])})" if item.get("turning_age") else ""
        badge = "🎉 <b>СЕГОДНЯ!</b>" if days_left == 0 else (f"⏳ <b>ЗАВТРА!</b>" if days_left == 1 else f"через {days_left} дн. ({next_dt})")
        note_str = f"\n   └ 🎁 <i>{note}</i>" if note else ""
        lines.append(f"{idx}. <b>{name}</b>{age_info} — {badge}{note_str}")

    await message.answer("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("today"))
@router.message(F.text == "🎂 Сегодня")
async def cmd_today(message: types.Message):
    items = get_sorted_birthdays()
    today_items = [b for b in items if b["days_left"] == 0]

    if not today_items:
        await message.answer("🍃 Сегодня ни у кого нет дня рождения.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    lines = ["🎂🎉 <b>СЕГОДНЯ ДЕНЬ РОЖДЕНИЯ!</b> 🎉🎂\n"]
    for item in today_items:
        name = item["name"]
        date_str = format_date_entry(item)
        note = item.get("note", "").strip()
        age_str = f" (исполняется <b>{format_age_word(item['turning_age'])}</b>!)" if item.get("turning_age") else ""
        note_str = f"\n🎁 <i>Заметка: {note}</i>" if note else ""
        lines.append(f"👤 <b>{name}</b>{age_str}\n🗓 {date_str}{note_str}")

    await message.answer("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("check"))
@router.message(F.text == "🔔 Проверить ДР")
async def cmd_check(message: types.Message):
    await message.answer("🔍 Проверяю базу и отправляю актуальные напоминания...")
    sent = check_and_notify(force_send=True, chat_id=message.chat.id)
    if sent:
        await message.answer(f"✅ Отправлено {len(sent)} напоминаний:\n• " + "\n• ".join(sent), reply_markup=get_main_menu())
    else:
        await message.answer("👌 На ближайшие дни напоминаний нет.", reply_markup=get_main_menu())
