import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.secret_vault.storage import (
    is_vault_initialized,
    is_vault_unlocked,
    set_user_pin,
    verify_pin,
    lock_vault,
    add_secret_note,
    get_secret_notes,
    delete_secret_note,
    user_vault_states
)

logger = logging.getLogger("SecretVaultHandlers")
router = Router(name="secret_vault")


def get_vault_keyboard(is_unlocked: bool = False, notes: list = None) -> InlineKeyboardMarkup:
    if not is_unlocked:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔓 Ввести PIN-код для входа", callback_data="v_prompt_pin")]
            ]
        )

    buttons = [
        [InlineKeyboardButton(text="➕ Добавить секрет / пароль", callback_data="v_add_prompt")]
    ]
    if notes:
        for n in notes[:8]:
            nid = n["id"]
            title = n["title"]
            buttons.append([
                InlineKeyboardButton(text=f"🔑 {title}", callback_data=f"v_view_{nid}"),
                InlineKeyboardButton(text="🗑", callback_data=f"v_del_{nid}")
            ])
    buttons.append([InlineKeyboardButton(text="🔒 Заблокировать сейф", callback_data="v_lock_now")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def is_in_vault_input_state(message: types.Message) -> bool:
    """Filter that ensures this router ONLY intercepts text when user is actively in a vault flow."""
    user_id = message.from_user.id if message.from_user else 0
    return user_id in user_vault_states


@router.message(Command("vault"))
@router.message(F.text == "🔐 Секретный сейф")
async def cmd_vault(message: types.Message):
    user_id = message.from_user.id

    if not is_vault_initialized(user_id):
        user_vault_states[user_id] = "SET_PIN"
        await message.answer(
            "🔐 <b>Добро пожаловать в Секретный Сейф!</b> 🛡️\n\n"
            "Ваш сейф ещё не защищён. Придумайте и отправьте прямо в чат **4-значный PIN-код** (например: <code>1234</code>):\n\n"
            "<i>(PIN-код будет захэширован по стандарту SHA-256 и известен только вам)</i>",
            parse_mode=ParseMode.HTML
        )
        return

    if is_vault_unlocked(user_id):
        notes = get_secret_notes(user_id)
        count = len(notes)
        text = (
            "🔓 <b>Секретный сейф открыт (активен 10 минут):</b>\n\n"
            f"📦 Сохранено секретных записей: <b>{count}</b>\n\n"
            "Выберите запись ниже, чтобы просмотреть, или добавьте новый секрет:"
        )
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_vault_keyboard(True, notes))
    else:
        user_vault_states[user_id] = "CHECK_PIN"
        await message.answer(
            "🔒 <b>Сейф заблокирован.</b>\n\n"
            "Отправьте ваш <b>PIN-код</b> в ответном сообщении для разблокировки:",
            parse_mode=ParseMode.HTML
        )


@router.callback_query(F.data == "v_prompt_pin")
async def callback_prompt_pin(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_vault_states[user_id] = "CHECK_PIN"
    await callback.message.answer("🔑 Отправьте ваш PIN-код в чат:", parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "v_lock_now")
async def callback_lock_now(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lock_vault(user_id)
    await callback.answer("Сейф заблокирован! 🔒")
    await callback.message.edit_text("🔒 <b>Сейф надёжно заблокирован.</b>", parse_mode=ParseMode.HTML, reply_markup=get_vault_keyboard(False))


@router.callback_query(F.data == "v_add_prompt")
async def callback_add_prompt(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_vault_unlocked(user_id):
        await callback.answer("Сначала разблокируйте сейф!", show_alert=True)
        return
    user_vault_states[user_id] = "ADD_NOTE"
    await callback.message.answer(
        "📝 <b>Добавление новой секретной записи</b>\n\n"
        "Отправьте текст в формате:\n"
        "<code>Заголовок | Секретные данные</code>\n\n"
        "<i>Примеры:</i>\n"
        "• <code>Wi-Fi дома | mySuperSecretPass2026</code>\n"
        "• <code>Карта Тинькофф | 2200 7000 1234 5678, CVC 789</code>\n"
        "• <code>Крипто-кошелек | 12 слов seed-фразы...</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("v_view_"))
async def callback_view_note(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_vault_unlocked(user_id):
        await callback.answer("Сейф заблокирован!", show_alert=True)
        return

    note_id = callback.data.replace("v_view_", "")
    notes = get_secret_notes(user_id)
    target = next((n for n in notes if str(n["id"]) == note_id), None)

    if not target:
        await callback.answer("Запись не найдена!", show_alert=True)
        return

    text = (
        f"🔑 <b>Секрет: {target['title']}</b>\n"
        f"🕒 <i>Создан: {target['created_at']}</i>\n\n"
        f"<code>{target['content']}</code>\n\n"
        "💡 <i>Нажмите на текст в рамке выше, чтобы скопировать.</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить запись", callback_data=f"v_del_{note_id}")],
            [InlineKeyboardButton(text="🔙 К списку сейфа", callback_data="v_refresh")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("v_del_"))
async def callback_del_note(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not is_vault_unlocked(user_id):
        await callback.answer("Сейф заблокирован!", show_alert=True)
        return

    note_id = callback.data.replace("v_del_", "")
    success = delete_secret_note(user_id, note_id)
    if success:
        await callback.answer("Запись удалена 🗑")
        notes = get_secret_notes(user_id)
        await callback.message.answer("✅ Секретная запись успешно удалена!", reply_markup=get_vault_keyboard(True, notes))
    else:
        await callback.answer("Ошибка удаления", show_alert=True)


@router.callback_query(F.data == "v_refresh")
async def callback_refresh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if is_vault_unlocked(user_id):
        notes = get_secret_notes(user_id)
        await callback.message.answer(
            f"🔓 <b>Секретный сейф (записей: {len(notes)}):</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_vault_keyboard(True, notes)
        )
    await callback.answer()


@router.message(F.text, is_in_vault_input_state)
async def handle_vault_text_input(message: types.Message):
    user_id = message.from_user.id
    state = user_vault_states.get(user_id)

    if not state:
        return

    text = message.text.strip()

    # 1. State: Setting Initial PIN
    if state == "SET_PIN":
        if not text.isdigit() or len(text) < 4:
            await message.answer("⚠️ PIN-код должен состоять минимум из 4 цифр (например <code>1234</code>):", parse_mode=ParseMode.HTML)
            return
        set_user_pin(user_id, text)
        del user_vault_states[user_id]
        notes = get_secret_notes(user_id)
        await message.answer(
            f"🎉 <b>PIN-код успешно установлен!</b> 🛡️\n\n"
            "Сейф разблокирован на 10 минут. Теперь вы можете сохранить свои пароли и секреты:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_vault_keyboard(True, notes)
        )
        return

    # 2. State: Verifying PIN
    if state == "CHECK_PIN":
        if verify_pin(user_id, text):
            del user_vault_states[user_id]
            notes = get_secret_notes(user_id)
            await message.answer(
                "🔓 <b>PIN-код верный! Сейф разблокирован.</b>\n\n"
                f"📦 Ваших записей: <b>{len(notes)}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=get_vault_keyboard(True, notes)
            )
        else:
            await message.answer("❌ <b>Неверный PIN-код!</b> Попробуйте ещё раз или введите /vault:", parse_mode=ParseMode.HTML)
        return

    # 3. State: Adding Note
    if state == "ADD_NOTE":
        if not is_vault_unlocked(user_id):
            del user_vault_states[user_id]
            await message.answer("🔒 Время сессии истекло. Откройте сейф заново через /vault")
            return

        if "|" in text:
            parts = text.split("|", 1)
            title = parts[0].strip()
            content = parts[1].strip()
        else:
            title = text[:20] + "..." if len(text) > 20 else text
            content = text

        note = add_secret_note(user_id, title, content)
        del user_vault_states[user_id]
        notes = get_secret_notes(user_id)

        await message.answer(
            f"✅ <b>Секрет «{note['title']}» сохранён в сейф!</b> 🔒",
            parse_mode=ParseMode.HTML,
            reply_markup=get_vault_keyboard(True, notes)
        )
        return
