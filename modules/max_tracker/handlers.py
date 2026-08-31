import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.max_tracker.storage import (
    get_user_max_config,
    set_user_max_config
)
from modules.max_tracker.checker import check_max_for_user

logger = logging.getLogger("MAXHandlers")
router = Router(name="max_tracker")

user_max_input_state: dict = {}


def get_max_keyboard(is_configured: bool = False, enabled: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if is_configured:
        buttons.append([
            InlineKeyboardButton(text="🔄 Проверить сейчас", callback_data="max_check_now"),
            InlineKeyboardButton(text="🔔 Алерт: ВКЛ" if enabled else "🔕 Алерт: ВЫКЛ", callback_data="max_toggle_alerts")
        ])
        buttons.append([
            InlineKeyboardButton(text="🔑 Обновить ключ / токен MAX", callback_data="max_prompt_token"),
            InlineKeyboardButton(text="❓ Где взять токен", callback_data="max_guide")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔑 Привязать токен MAX", callback_data="max_prompt_token"),
            InlineKeyboardButton(text="❓ Инструкция: где взять", callback_data="max_guide")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("max"))
@router.message(Command("max_check"))
@router.message(F.text == "💬 MAX Уведомления")
async def cmd_max_dashboard(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    config = get_user_max_config(user_id)
    token = (config.get("token") if config else "") or ""
    enabled = config.get("enabled", True) if config else True

    if not token:
        intro = (
            "💬 <b>Мониторинг мессенджера MAX (web.max.ru)</b> 🔔\n\n"
            "Бот умеет в реальном времени проверять ваши сообщения в MAX и присылать пуши в Telegram:\n"
            "• ✉️ Новые входящие сообщения в диалогах и группах\n"
            "• 💬 Количество непрочитанных чатов\n"
            "• 🔔 Уведомления и упоминания\n\n"
            "⚙️ <b>Как настроить за 30 секунд:</b>\n"
            "Отправьте команду с вашим токеном или значением <code>__oneme_auth</code>:\n"
            "<code>/max_token ВАШ_ТОКЕН</code>\n\n"
            "<i>(Или нажмите кнопку «Инструкция» ниже для пошаговой подсказки)</i>."
        )
        await message.answer(intro, parse_mode=ParseMode.HTML, reply_markup=get_max_keyboard(False, enabled))
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    report = await check_max_for_user(user_id, bot, notify_only_new=False)

    if report:
        await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=get_max_keyboard(True, enabled), disable_web_page_preview=True)
    else:
        await message.answer("⚠️ Не удалось получить данные от MAX. Попробуйте нажать «Проверить сейчас».", reply_markup=get_max_keyboard(True, enabled))


@router.message(Command("max_token"))
@router.message(Command("max_cookie"))
async def cmd_set_max_token(message: types.Message):
    user_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        user_max_input_state[user_id] = True
        await message.answer(
            "🔑 <b>Привязка токена мессенджера MAX:</b>\n\n"
            "Отправьте значение токена (или строку <code>__oneme_auth</code> из LocalStorage) ответным сообщением в чат:",
            parse_mode=ParseMode.HTML
        )
        return

    raw_token = parts[1].strip()
    set_user_max_config(user_id, token=raw_token, enabled=True)
    if user_id in user_max_input_state:
        del user_max_input_state[user_id]

    await message.answer(
        "✅ <b>Токен мессенджера MAX успешно сохранён!</b> 🛡️💬\n\n"
        "Бот начал автоматический мониторинг сообщений MAX каждые 60 секунд 24/7!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "max_check_now")
async def callback_max_check_now(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    report = await check_max_for_user(user_id, bot, notify_only_new=False)
    if report:
        try:
            await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=get_max_keyboard(True, True), disable_web_page_preview=True)
        except Exception:
            pass
        await callback.answer("Данные MAX обновлены! 🔄")
    else:
        await callback.answer("Ошибка обновления MAX", show_alert=True)


@router.callback_query(F.data == "max_toggle_alerts")
async def callback_max_toggle_alerts(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    config = get_user_max_config(user_id) or {}
    new_state = not config.get("enabled", True)
    set_user_max_config(user_id, enabled=new_state)

    state_str = "включены 🔔" if new_state else "отключены 🔕"
    await callback.answer(f"Уведомления MAX {state_str}")
    await callback.message.edit_reply_markup(reply_markup=get_max_keyboard(bool(config.get("token")), new_state))


@router.callback_query(F.data == "max_prompt_token")
async def callback_max_prompt_token(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_max_input_state[user_id] = True
    await callback.message.answer(
        "🔑 <b>Отправьте ваш токен авторизации MAX (или скопированный __oneme_auth):</b>\n\n"
        "<code>/max_token ВСТАВЬТЕ_ЗНАЧЕНИЕ</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "max_guide")
async def callback_max_guide(callback: types.CallbackQuery):
    guide_text = (
        "📖 <b>Как скопировать токен из web.max.ru за 30 секунд:</b>\n\n"
        "1. Откройте в браузере сайт <a href='https://web.max.ru/'>web.max.ru</a> со своего аккаунта.\n"
        "2. Нажмите <b>F12</b> (Инструменты разработчика).\n"
        "3. Перейдите во вкладку <b>Application</b> (Приложение) ➔ слева откройте <b>Local Storage</b> ➔ <code>https://web.max.ru</code>.\n"
        "4. Найдите строку с ключом <b><code>__oneme_auth</code></b> и дважды кликните на значение, чтобы скопировать.\n"
        "5. Отправьте боту команду:\n"
        "<code>/max_token СКОПИРОВАННЫЙ_ТЕКСТ</code>\n\n"
        "🔒 <i>Токен сохраняется в зашифрованном виде и используется только для проверки счетчиков непрочитанных сообщений.</i>"
    )
    await callback.message.answer(guide_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()
