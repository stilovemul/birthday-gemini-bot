import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.vk_tracker.storage import (
    get_user_vk_config,
    set_user_vk_config
)
from modules.vk_tracker.checker import fetch_vk_updates, check_vk_for_user

logger = logging.getLogger("VKHandlers")
router = Router(name="vk_tracker")

user_vk_input_state: dict = {}


def get_vk_keyboard(is_configured: bool = False, enabled: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if is_configured:
        buttons.append([
            InlineKeyboardButton(text="🔄 Проверить сейчас", callback_data="vk_check_now"),
            InlineKeyboardButton(text="🔔 Алерт: ВКЛ" if enabled else "🔕 Алерт: ВЫКЛ", callback_data="vk_toggle_alerts")
        ])
        buttons.append([
            InlineKeyboardButton(text="🔑 Обновить токен VK", callback_data="vk_prompt_token")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔑 Привязать токен VK", callback_data="vk_prompt_token"),
            InlineKeyboardButton(text="❓ Инструкция: где взять", callback_data="vk_guide")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("vk"))
@router.message(Command("vk_check"))
@router.message(F.text == "🔵 VK Уведомления")
async def cmd_vk_dashboard(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    config = get_user_vk_config(user_id)
    token = (config.get("token") if config else "") or ""
    enabled = config.get("enabled", True) if config else True

    if not token:
        intro = (
            "🔵 <b>Мониторинг событий и сообщений ВКонтакте (VK)</b> 🔔\n\n"
            "Бот умеет в реальном времени проверять ваш профиль VK и присылать пуши в Telegram:\n"
            "• ✉️ Новые личные сообщения в диалогах\n"
            "• 🔔 Уведомления, лайки, комментарии и реакции\n"
            "• 👥 Новые заявки в друзья\n\n"
            "⚙️ <b>Как настроить за 30 секунд:</b>\n"
            "Отправьте команду с вашим токеном VK:\n"
            "<code>/vk_token ВАШ_ТОКЕН</code>"
        )
        await message.answer(intro, parse_mode=ParseMode.HTML, reply_markup=get_vk_keyboard(False, enabled))
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    report = await check_vk_for_user(user_id, bot, notify_only_new=False)

    if report:
        await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=get_vk_keyboard(True, enabled))
    else:
        await message.answer("⚠️ Не удалось получить данные от VK. Попробуйте нажать «Проверить сейчас».", reply_markup=get_vk_keyboard(True, enabled))


@router.message(Command("vk_token"))
async def cmd_set_vk_token(message: types.Message):
    user_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        user_vk_input_state[user_id] = True
        await message.answer(
            "🔑 <b>Привязка токена ВКонтакте (VK):</b>\n\n"
            "Отправьте ваш токен доступа VK (access_token) ответным сообщением в чат:",
            parse_mode=ParseMode.HTML
        )
        return

    raw_token = parts[1].strip()
    if "access_token=" in raw_token:
        try:
            token_val = raw_token.split("access_token=")[1].split("&")[0]
        except Exception:
            token_val = raw_token
    else:
        token_val = raw_token

    set_user_vk_config(user_id, token=token_val, enabled=True)
    if user_id in user_vk_input_state:
        del user_vk_input_state[user_id]

    await message.answer(
        "✅ <b>Токен ВКонтакте успешно сохранён!</b> 🛡️🔵\n\n"
        "Бот начал автоматический мониторинг сообщений и уведомлений VK каждые 60 секунд!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "vk_check_now")
async def callback_vk_check_now(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    report = await check_vk_for_user(user_id, bot, notify_only_new=False)
    if report:
        try:
            await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=get_vk_keyboard(True, True))
        except Exception:
            pass
        await callback.answer("Данные VK обновлены! 🔄")
    else:
        await callback.answer("Ошибка обновления VK", show_alert=True)


@router.callback_query(F.data == "vk_toggle_alerts")
async def callback_vk_toggle_alerts(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    config = get_user_vk_config(user_id) or {}
    new_state = not config.get("enabled", True)
    set_user_vk_config(user_id, enabled=new_state)

    state_str = "включены 🔔" if new_state else "отключены 🔕"
    await callback.answer(f"Уведомления VK {state_str}")
    await callback.message.edit_reply_markup(reply_markup=get_vk_keyboard(bool(config.get("token")), new_state))


@router.callback_query(F.data == "vk_prompt_token")
async def callback_vk_prompt_token(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_vk_input_state[user_id] = True
    await callback.message.answer(
        "🔑 <b>Отправьте ваш access_token ВКонтакте в ответном сообщении:</b>\n\n"
        "<i>(Токен будет сохранён в защищённой базе и будет использоваться для проверки счетчиков)</i>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "vk_guide")
async def callback_vk_guide(callback: types.CallbackQuery):
    guide_text = (
        "📖 <b>Как получить access_token ВКонтакте:</b>\n\n"
        "1. Откройте прямую ссылку авторизации: <a href='https://oauth.vk.com/authorize?client_id=2685278&scope=friends,messages,notifications,offline&response_type=token&v=5.199'>Получить токен VK</a>\n"
        "2. Нажмите «Разрешить»\n"
        "3. Скопируйте ссылку из адресной строки и отправьте её боту:\n"
        "<code>/vk_token ВАШ_ТОКЕН</code>"
    )
    await callback.message.answer(guide_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()
