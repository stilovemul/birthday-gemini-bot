import json
import uuid
from datetime import datetime
from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from core.config import NOTES_FILE, MSK_TZ
from core.keyboards import get_main_menu

router = Router(name="notes")


def load_notes():
    if not NOTES_FILE.exists():
        save_notes([])
        return []
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_notes(notes):
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


@router.message(Command("note"))
async def cmd_add_note(message: types.Message):
    text = (message.text or "").replace("/note", "", 1).strip()
    if not text:
        await message.answer("📝 Формат: <code>/note Купить билеты в театр</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    notes = load_notes()
    new_note = {
        "id": str(uuid.uuid4())[:6],
        "text": text,
        "created_at": datetime.now(MSK_TZ).strftime("%d.%m %H:%M")
    }
    notes.append(new_note)
    save_notes(notes)
    await message.answer(f"✅ <b>Заметка сохранена:</b>\n«{text}»\n<i>(ID: <code>{new_note['id']}</code>)</i>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("notes"))
@router.message(F.text == "📝 Заметки")
async def cmd_list_notes(message: types.Message):
    notes = load_notes()
    if not notes:
        await message.answer("📭 У вас пока нет сохраненных заметок.\nДобавьте: <code>/note Текст заметки</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    lines = ["📝 <b>Ваши заметки и задачи:</b>\n"]
    for idx, n in enumerate(notes, 1):
        lines.append(f"{idx}. <b>{n['text']}</b>\n   └ 🕒 {n['created_at']} <code>[id:{n['id']}]</code>")

    lines.append("\n💡 <i>Чтобы удалить заметку, введите:</i> <code>/delnote ID</code>")
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("delnote"))
async def cmd_del_note(message: types.Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажите ID: <code>/delnote a1b2c3</code>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    target_id = parts[1].strip().lower()
    notes = load_notes()
    filtered = [n for n in notes if n["id"].lower() != target_id]

    if len(filtered) == len(notes):
        await message.answer(f"❌ Заметка с ID <code>{target_id}</code> не найдена.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    save_notes(filtered)
    await message.answer("🗑 Заметка успешно удалена.", reply_markup=get_main_menu())
