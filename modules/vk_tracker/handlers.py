import logging
import re
import html
import aiohttp
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.vk_tracker.storage import (
    get_user_vk_config,
    set_user_vk_config
)
from modules.vk_tracker.checker import fetch_vk_updates, check_vk_for_user, VK_API_VERSION

logger = logging.getLogger("VKHandlers")
router = Router(name="vk_tracker")

user_vk_input_state: dict = {}

OAUTH_ANDROID_URL = "https://oauth.vk.com/authorize?client_id=2274003&scope=friends,messages,photos,video,docs,notes,wall,groups,notifications,offline&response_type=token&v=5.199"
OAUTH_VKME_URL = "https://oauth.vk.com/authorize?client_id=6146827&scope=friends,messages,photos,video,docs,notes,wall,groups,notifications,offline&response_type=token&v=5.199"
OAUTH_IPAD_URL = "https://oauth.vk.com/authorize?client_id=3140623&scope=friends,messages,photos,video,docs,notes,wall,groups,notifications,offline&response_type=token&v=5.199"


def get_vk_keyboard(is_configured: bool = False, enabled: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if is_configured:
        buttons.append([
            InlineKeyboardButton(text="🔄 Проверить сейчас", callback_data="vk_check_now"),
            InlineKeyboardButton(text="🔔 Алерт: ВКЛ" if enabled else "🔕 Алерт: ВЫКЛ", callback_data="vk_toggle_alerts")
        ])
        buttons.append([
            InlineKeyboardButton(text="🔑 Обновить токен VK", callback_data="vk_prompt_token"),
            InlineKeyboardButton(text="❓ Инструкция", callback_data="vk_guide")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔑 Привязать токен VK", callback_data="vk_prompt_token"),
            InlineKeyboardButton(text="❓ Инструкция: где взять", callback_data="vk_guide")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def extract_vk_token_from_text(raw_text: str) -> str:
    """Extracts clean VK access_token from raw text, query string, or redirect URL."""
    text = (raw_text or "").strip()
    if "access_token=" in text:
        match = re.search(r'access_token=([a-zA-Z0-9_\.\-]+)', text)
        if match:
            return match.group(1).split('&')[0]
    # Check if raw modern token vk1.a... or legacy 85-char hex
    vk1_match = re.search(r'(vk1\.a\.[a-zA-Z0-9_\-]+)', text)
    if vk1_match:
        return vk1_match.group(1)
    # Check words
    parts = text.split()
    for p in parts:
        if p.startswith("vk1.a."):
            return p
    return text.strip()


async def validate_vk_token(token: str) -> tuple[bool, dict, str]:
    """Validates token by querying VK users.get."""
    if not token:
        return False, {}, "Пустой токен."
    url = f"https://api.vk.com/method/users.get?v={VK_API_VERSION}&access_token={token}"
    headers = {"User-Agent": "KateMobileAndroid/113.1 lite-548 (Android 14; SDK 34; arm64-v8a; samsung SM-S928B; ru)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                data = await resp.json()
                if "error" in data:
                    err = data["error"]
                    code = err.get("error_code", 0)
                    msg = err.get("error_msg", "Ошибка доступа")
                    if code == 9:
                        return False, {}, "VK вернул ошибку Flood control (ограничение частоты запросов к токену). Получите новый токен по ссылке VK Android."
                    return False, {}, f"Ошибка VK ({code}): {msg}"
                items = data.get("response", [])
                if items and isinstance(items, list):
                    u = items[0]
                    return True, u, "OK"
                return False, {}, "Не удалось получить профиль пользователя."
    except Exception as e:
        return False, {}, f"Сетевая ошибка при проверке: {e}"


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
            "Бот проверяет ваш профиль VK 24/7 и присылает пуши в Telegram:\n"
            "• ✉️ Новые входящие диалоги и текст сообщений\n"
            "• 🔔 Уведомления, лайки, комментарии и реакции\n"
            "• 👥 Новые заявки в друзья\n\n"
            "⚙️ <b>Как настроить за 30 секунд:</b>\n"
            "1. Нажмите «🔑 Привязать токен VK» или «❓ Инструкция: где взять»\n"
            "2. Перейдите по ссылке авторизации и скопируйте адресную строку\n"
            "3. Отправьте скопированный текст боту!"
        )
        await message.answer(intro, parse_mode=ParseMode.HTML, reply_markup=get_vk_keyboard(False, enabled))
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    report = await check_vk_for_user(user_id, bot, notify_only_new=False)

    if report:
        await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=get_vk_keyboard(True, enabled), disable_web_page_preview=True)
    else:
        await message.answer("⚠️ Не удалось получить данные от VK. Попробуйте нажать «Проверить сейчас».", reply_markup=get_vk_keyboard(True, enabled))


@router.message(Command("vk_token"))
async def cmd_set_vk_token(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        user_vk_input_state[user_id] = True
        guide_text = (
            "🔑 <b>Привязка токена ВКонтакте (VK):</b>\n\n"
            "1. Откройте ссылку авторизации: <a href='" + OAUTH_ANDROID_URL + "'><b>Получить токен VK Android</b></a>\n"
            "   <i>(Запасная ссылка: <a href='" + OAUTH_VKME_URL + "'>VK Me</a>)</i>\n"
            "2. Нажмите <b>«Разрешить»</b>\n"
            "3. Скопируйте адрес из адресной строки браузера (там будет <code>access_token=...</code>) и <b>отправьте его сюда в чат</b>:"
        )
        await message.answer(guide_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return

    await process_vk_token_input(message, parts[1].strip(), bot)


async def process_vk_token_input(message: types.Message, raw_input: str, bot: Bot):
    user_id = message.from_user.id
    token_val = extract_vk_token_from_text(raw_input)

    if not token_val:
        await message.answer("⚠️ Не удалось распознать токен. Пожалуйста, отправьте ссылку целиком или сам токен.")
        return

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ok, user_data, err_desc = await validate_vk_token(token_val)

    if not ok:
        await message.answer(
            f"❌ <b>Ошибка проверки токена:</b>\n\n"
            f"<code>{html.escape(err_desc)}</code>\n\n"
            f"💡 <b>Попробуйте открыть ссылку VK Android и нажать «Разрешить»:</b>\n"
            f"👉 <a href='{OAUTH_ANDROID_URL}'>Ссылка авторизации VK Android</a>\n"
            f"👉 <a href='{OAUTH_VKME_URL}'>Запасная ссылка VK Me</a>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return

    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    vk_uid = user_data.get("id", "")
    full_name = f"{first_name} {last_name}".strip() or "Олег Уринев"

    set_user_vk_config(
        user_id=user_id,
        token=token_val,
        user_id_vk=str(vk_uid),
        user_name=full_name,
        enabled=True
    )
    if user_id in user_vk_input_state:
        del user_vk_input_state[user_id]

    # Fetch live check
    report = await check_vk_for_user(user_id, bot, notify_only_new=False)

    success_msg = (
        f"✅ <b>Токен ВКонтакте успешно подключён и проверен!</b> 🛡️🔵\n\n"
        f"👤 <b>Профиль:</b> {html.escape(full_name)} (id{vk_uid})\n"
        f"⚡ <b>Автопроверка 24/7:</b> включена (каждые 60 секунд)\n\n"
        + (report or "")
    )
    await message.answer(
        success_msg,
        parse_mode=ParseMode.HTML,
        reply_markup=get_vk_keyboard(True, True),
        disable_web_page_preview=True
    )


@router.message(F.text.startswith("vk1.a.") | F.text.contains("oauth.vk.com/blank.html#access_token=") | F.text.contains("oauth.vk.ru/blank.html#access_token=") | F.text.contains("access_token=vk1.a."))
async def handle_direct_token_paste(message: types.Message, bot: Bot):
    await process_vk_token_input(message, message.text, bot)


@router.callback_query(F.data == "vk_check_now")
async def callback_vk_check_now(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    report = await check_vk_for_user(user_id, bot, notify_only_new=False)
    if report:
        try:
            await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=get_vk_keyboard(True, True), disable_web_page_preview=True)
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
    guide_text = (
        "🔑 <b>Привязка / Обновление токена ВКонтакте (VK):</b>\n\n"
        "1. Перейдите по ссылке авторизации: <a href='" + OAUTH_ANDROID_URL + "'><b>Получить токен VK Android</b></a>\n"
        "   <i>(Либо <a href='" + OAUTH_VKME_URL + "'>VK Me</a>)</i>\n"
        "2. Нажмите <b>«Разрешить»</b>\n"
        "3. Скопируйте адресную строку из браузера и <b>просто отправьте её ответным сообщением сюда в чат</b>!"
    )
    await callback.message.answer(guide_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "vk_guide")
async def callback_vk_guide(callback: types.CallbackQuery):
    guide_text = (
        "📖 <b>Как получить access_token ВКонтакте за 30 секунд:</b>\n\n"
        "🔹 <b>Вариант 1 (Основной - VK Android):</b>\n"
        "👉 <a href='" + OAUTH_ANDROID_URL + "'><b>Нажмите здесь для получения токена VK Android</b></a>\n\n"
        "🔹 <b>Вариант 2 (VK Me):</b>\n"
        "👉 <a href='" + OAUTH_VKME_URL + "'><b>Ссылка авторизации VK Me</b></a>\n\n"
        "🔹 <b>Вариант 3 (VK iPad):</b>\n"
        "👉 <a href='" + OAUTH_IPAD_URL + "'><b>Ссылка авторизации VK iPad</b></a>\n\n"
        "<b>Шаги:</b>\n"
        "1. Перейдите по любой ссылке выше в браузере.\n"
        "2. Нажмите кнопку <b>«Разрешить»</b>.\n"
        "3. В адресной строке откроется страница с адресом <code>https://oauth.vk.com/blank.html#access_token=...</code>.\n"
        "4. Скопируйте весь текст из адресной строки и <b>отправьте его боту в этот чат</b>!"
    )
    await callback.message.answer(guide_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await callback.answer()

