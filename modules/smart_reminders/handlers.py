import re
from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from core.keyboards import get_main_menu
from modules.smart_reminders.storage import add_reminder, get_active_reminders, delete_reminder
from modules.smart_reminders.parser import parse_natural_reminder

router = Router(name="smart_reminders")


@router.message(Command("remind"))
async def cmd_remind(message: types.Message):
    text = (message.text or "").strip()
    raw = re.sub(r"^/remind\s*", "", text, flags=re.IGNORECASE).strip()
    if not raw:
        help_text = (
            "⏰ <b>Умные напоминания обычными словами:</b>\n\n"
            "Напишите команду и задачу с указанием времени:\n\n"
            "• <code>/remind завтра в 15:00 позвонить в автосервис</code>\n"
            "• <code>/remind через 45 минут выключить духовку</code>\n"
            "• <code>/remind 5 сентября в 11:30 встреча с юристом</code>\n\n"
            "Или просто напишите боту в чат: <i>«Напомни вечером в 19:30 купить хлеб»</i>"
        )
        await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    success, target_dt, task_text, info = await parse_natural_reminder(raw)
    if success and target_dt:
        item = add_reminder(message.from_user.id, task_text, target_dt)
        time_formatted = target_dt.strftime("%d.%m.%Y в %H:%M MSK")
        reply = (
            f"✅ <b>Напоминание установлено!</b>\n\n"
            f"📌 <b>Задача:</b> {task_text}\n"
            f"🕒 <b>Время:</b> {time_formatted}\n"
            f"<i>(ID: <code>{item['id']}</code>)</i>"
        )
        await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
    else:
        await message.answer(f"❌ {info}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("reminders"))
@router.message(F.text == "⏰ Напоминания")
async def cmd_list_reminders(message: types.Message):
    items = get_active_reminders(message.from_user.id)
    if not items:
        await message.answer(
            "📭 У вас нет активных напоминаний.\n\n"
            "Чтобы создать напоминание, напишите:\n"
            "<code>/remind завтра в 15:00 позвонить коллеге</code>\n"
            "или просто: <i>«Напомни через 20 минут проверить духовку»</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    lines = [f"⏰ <b>Ваши активные напоминания ({len(items)}):</b>\n"]
    for idx, r in enumerate(items, 1):
        lines.append(f"{idx}. 📌 <b>{r['text']}</b>\n   └ 🕒 {r['target_display']} <code>[id:{r['id']}]</code>")

    lines.append("\n💡 <i>Чтобы отменить напоминание:</i> <code>/delremind ID</code>")
    await message.answer("\n\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("delremind"))
async def cmd_del_reminder(message: types.Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажите ID: <code>/delremind a1b2c3</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    target_id = parts[1].strip()
    if delete_reminder(target_id):
        await message.answer(f"🗑 Напоминание <code>{target_id}</code> отменено.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
    else:
        await message.answer(f"❌ Напоминание с ID <code>{target_id}</code> не найдено.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
