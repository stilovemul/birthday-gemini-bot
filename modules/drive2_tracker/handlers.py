import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.drive2_tracker.storage import (
    get_user_drive2_config,
    set_user_drive2_config
)
from modules.drive2_tracker.checker import check_user_drive2

logger = logging.getLogger("Drive2Handlers")
router = Router(name="drive2_tracker")


def get_drive2_control_keyboard(is_enabled: bool = True) -> InlineKeyboardMarkup:
    toggle_text = "⏸ Приостановить" if is_enabled else "▶️ Включить мониторинг"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Проверить сейчас", callback_data="d2_check_now"),
                InlineKeyboardButton(text=toggle_text, callback_data="d2_toggle_state")
            ],
            [
                InlineKeyboardButton(text="🔑 Обновить куки .AST", callback_data="d2_cookie_help")
            ]
        ]
    )


@router.message(Command("drive2"))
@router.message(F.text == "🚗 Drive2 Уведомления")
async def cmd_drive2_status(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    config = get_user_drive2_config(user_id)

    if not config or (not config.get("cookies") and not config.get("profile_url")):
        help_text = (
            "🚗 <b>Мониторинг событий Drive2.ru</b> 🔔\n\n"
            "Бот умеет проверять ваш аккаунт на Drive2.ru и присылать уведомления в Telegram:\n"
            "• 📩 <b>Новые личные сообщения</b> в диалогах\n"
            "• 👤 <b>Новые подписчики</b> на профиль и машины\n"
            "• 💬 <b>Комментарии, ответы и лайки в бортжурнале</b>\n\n"
            "⚙️ <b>Как настроить за 1 минуту:</b>\n"
            "1. Отправьте команду с вашей кукой авторизации:\n"
            "<code>/drive2_cookie ВАША_КУКА</code>\n\n"
            "<i>(Или нажмите кнопку ниже для подробной инструкции)</i>."
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Инструкция: где взять куки", callback_data="d2_cookie_help")]
            ]
        )
        await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    is_enabled = config.get("enabled", True)
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Perform live real-time check against Drive2
    success, report = await check_user_drive2(user_id, bot, notify_if_no_change=True)
    cfg_updated = get_user_drive2_config(user_id) or config

    if success:
        cur_msgs = cfg_updated.get("last_messages", 0)
        cur_notifs = cfg_updated.get("last_notifications", 0)

        text = (
            "🚗 <b>Центр мониторинга Drive2.ru</b>\n\n"
            f"📊 <b>Состояние:</b> {'🟢 Активен (проверка каждые 60с)' if is_enabled else '⏸ На паузе'}\n"
            f"🔐 <b>Авторизация:</b> 🔑 Сессия активна (Олег / manofftoday)\n\n"
            "📬 <b>Текущие счетчики в реальном времени:</b>\n"
            f"• 📩 Непрочитанных сообщений: <b>{cur_msgs}</b>\n"
            f"• 🔔 Новых уведомлений / событий: <b>{cur_notifs}</b>\n\n"
            + ("✨ <i>Все входящие прочитаны!</i>" if (cur_msgs == 0 and cur_notifs == 0) else "⚡ <i>Есть новые входящие на сайте!</i>")
            + "\n\n🔗 <a href='https://www.drive2.ru/my/messages/'>Открыть сообщения на Drive2</a> | <a href='https://www.drive2.ru/my/notifications/'>Уведомления</a>"
        )
        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_drive2_control_keyboard(is_enabled), disable_web_page_preview=True)
    else:
        await message.answer(
            f"⚠️ <b>Внимание:</b>\n{report}",
            parse_mode=ParseMode.HTML,
            reply_markup=get_drive2_control_keyboard(is_enabled)
        )


@router.message(Command("drive2_cookie"))
async def cmd_set_drive2_cookie(message: types.Message, bot: Bot):
    args = (message.text or "").split(maxsplit=1)
    user_id = message.from_user.id

    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "⚠️ <b>Укажите значение куки:</b>\n"
            "Пример:\n"
            "<code>/drive2_cookie .AST=AhQDQVNTVA...</code>\n\n"
            "<i>(Подробнее: нажмите /drive2 -> «Как привязать куки»)</i>",
            parse_mode=ParseMode.HTML
        )
        return

    cookie_val = args[1].strip()
    set_user_drive2_config(user_id, cookies=cookie_val, enabled=True)

    status_msg = await message.answer("🔍 <i>Проверяю подключение к вашему аккаунту Drive2.ru...</i>", parse_mode=ParseMode.HTML)
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    success, msg = await check_user_drive2(user_id, bot, notify_if_no_change=True)
    try:
        await status_msg.delete()
    except Exception:
        pass

    if success:
        cfg = get_user_drive2_config(user_id) or {}
        await message.answer(
            "🎉 <b>Drive2.ru успешно подключен!</b> 🚀\n\n"
            f"📩 Непрочитанных сообщений: <b>{cfg.get('last_messages', 0)}</b>\n"
            f"🔔 Уведомлений: <b>{cfg.get('last_notifications', 0)}</b>\n\n"
            "Бот автоматически проверяет сайт каждые 60 секунд 24/7!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            f"⚠️ <b>Внимание:</b> {msg}\n"
            "Проверьте правильность скопированной куки.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data == "d2_check_now")
async def callback_drive2_check_now(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    success, msg = await check_user_drive2(user_id, bot, notify_if_no_change=True)
    cfg = get_user_drive2_config(user_id) or {}
    is_enabled = cfg.get("enabled", True)

    if success:
        cur_msgs = cfg.get("last_messages", 0)
        cur_notifs = cfg.get("last_notifications", 0)
        text = (
            "🚗 <b>Центр мониторинга Drive2.ru</b>\n\n"
            f"📊 <b>Состояние:</b> {'🟢 Активен (проверка каждые 60с)' if is_enabled else '⏸ На паузе'}\n"
            f"🔐 <b>Авторизация:</b> 🔑 Сессия активна (Олег / manofftoday)\n\n"
            "📬 <b>Текущие счетчики:</b>\n"
            f"• 📩 Непрочитанных сообщений: <b>{cur_msgs}</b>\n"
            f"• 🔔 Новых уведомлений / событий: <b>{cur_notifs}</b>\n\n"
            + ("✨ <i>Все входящие прочитаны!</i>" if (cur_msgs == 0 and cur_notifs == 0) else "⚡ <i>Есть новые входящие на сайте!</i>")
            + "\n\n🔗 <a href='https://www.drive2.ru/my/messages/'>Открыть сообщения на Drive2</a> | <a href='https://www.drive2.ru/my/notifications/'>Уведомления</a>"
        )
        try:
            await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_drive2_control_keyboard(is_enabled), disable_web_page_preview=True)
        except Exception:
            pass
        await callback.answer("Данные Drive2 обновлены! 🔄")
    else:
        await callback.answer(f"Ошибка: {msg}", show_alert=True)


@router.callback_query(F.data == "d2_toggle_state")
async def callback_drive2_toggle(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    config = get_user_drive2_config(user_id) or {}
    new_state = not config.get("enabled", True)
    set_user_drive2_config(user_id, enabled=new_state)

    state_text = "возобновлён 🟢" if new_state else "поставлен на паузу ⏸"
    await callback.answer(f"Мониторинг {state_text}")
    await callback.message.edit_reply_markup(reply_markup=get_drive2_control_keyboard(new_state))


@router.callback_query(F.data == "d2_cookie_help")
async def callback_cookie_help(callback: types.CallbackQuery):
    help_text = (
        "🔑 <b>Как получить куки Drive2 за 30 секунд:</b>\n\n"
        "1. Откройте сайт <a href='https://www.drive2.ru'>drive2.ru</a> на компьютере под своим аккаунтом.\n"
        "2. Нажмите клавишу <b>F12</b> (или правой кнопкой мыши -> <i>Посмотреть код</i>).\n"
        "3. Перейдите во вкладку <b>Application</b> (Приложение) -> слева выберите <b>Cookies</b> -> <b>https://www.drive2.ru</b>.\n"
        "4. Найдите строку <b>.AST</b>.\n"
        "5. Отправьте боту команду:\n"
        "<code>/drive2_cookie .AST=ВСТАВЬТЕ_ЗНАЧЕНИЕ</code>\n\n"
        "🔒 <i>Куки сохраняются в защищенном хранилище бота и используются исключительно для чтения счетчиков ваших уведомлений.</i>"
    )
    await callback.message.answer(help_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()
