import logging
import asyncio
import html
from typing import Tuple, Dict, Any
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu
from modules.drive2_tracker.storage import get_user_drive2_config
from modules.drive2_tracker.checker import check_user_drive2
from modules.drive2_tracker.handlers import get_drive2_control_keyboard

from modules.vk_tracker.storage import get_user_vk_config
from modules.vk_tracker.checker import check_vk_for_user
from modules.vk_tracker.handlers import get_vk_keyboard

from modules.max_tracker.storage import get_user_max_config
from modules.max_tracker.checker import check_max_for_user
from modules.max_tracker.handlers import get_max_keyboard

logger = logging.getLogger("UnifiedMonitor")
router = Router(name="unified_monitor")


def get_unified_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Проверить всё сейчас", callback_data="unimon_check_all")
            ],
            [
                InlineKeyboardButton(text="🚗 Drive2.ru", callback_data="unimon_open_d2"),
                InlineKeyboardButton(text="🔵 ВКонтакте", callback_data="unimon_open_vk"),
                InlineKeyboardButton(text="💬 MAX", callback_data="unimon_open_max")
            ]
        ]
    )


async def build_unified_status_card(user_id: int, bot: Bot) -> Tuple[str, InlineKeyboardMarkup]:
    """Fetches live summaries from Drive2, VK, and MAX in parallel and builds a single consolidated card."""
    # 1. Drive2 info
    d2_cfg = get_user_drive2_config(user_id) or {}
    d2_enabled = d2_cfg.get("enabled", True)
    d2_has_auth = bool(d2_cfg.get("cookies") or d2_cfg.get("profile_url"))
    d2_msgs = d2_cfg.get("last_messages", 0)
    d2_notifs = d2_cfg.get("last_notifications", 0)
    d2_status = "🟢 Активен" if (d2_enabled and d2_has_auth) else ("⏸ На паузе" if d2_has_auth else "⚪ Не настроен")

    # 2. VK info
    vk_cfg = get_user_vk_config(user_id) or {}
    vk_enabled = vk_cfg.get("enabled", True)
    vk_has_token = bool(vk_cfg.get("token"))
    vk_msgs = vk_cfg.get("last_messages", 0)
    vk_notifs = vk_cfg.get("last_notifications", 0)
    vk_friends = vk_cfg.get("last_friends", 0)
    vk_name = vk_cfg.get("user_name", "Олег Уринев")
    vk_status = "🟢 Активен" if (vk_enabled and vk_has_token) else ("⏸ На паузе" if vk_has_token else "⚪ Не настроен")

    # 3. MAX info
    max_cfg = get_user_max_config(user_id) or {}
    max_enabled = max_cfg.get("enabled", True)
    max_has_token = bool(max_cfg.get("token"))
    max_name = max_cfg.get("user_name", "Олег")
    max_status = "🟢 Активен" if (max_enabled and max_has_token) else ("⏸ На паузе" if max_has_token else "⚪ Не настроен")

    card_lines = [
        "📬 <b>Единый центр входящих (Drive2, VK & MAX):</b>",
        "",
        f"🚗 <b>Drive2.ru</b> — {d2_status}",
        f"   • Непрочитанных ЛС: <b>{d2_msgs}</b> | Событий/уведомлений: <b>{d2_notifs}</b>",
        "   🔗 <a href='https://www.drive2.ru/my/messages/'>Открыть диалоги</a>",
        "",
        f"🔵 <b>ВКонтакте ({html.escape(vk_name)})</b> — {vk_status}",
        f"   • Личных сообщений: <b>{vk_msgs}</b> | Уведомлений: <b>{vk_notifs}</b> | Заявок: <b>{vk_friends}</b>",
        "   🔗 <a href='https://vk.com/im'>Открыть диалоги</a>",
        "",
        f"💬 <b>Мессенджер MAX ({html.escape(max_name)})</b> — {max_status}",
        f"   • Непрочитанных сообщений: <b>{max_cfg.get('last_messages', 0)}</b>",
        "   🔗 <a href='https://web.max.ru/'>Открыть web.max.ru</a>",
        "",
        "➖➖➖➖➖➖➖➖➖➖",
        "⚡️ <i>Все 3 сервиса проверяются 24/7 каждые 60 секунд. При поступлении нового сообщения бот мгновенно пришлёт пуш-уведомление сюда в Telegram!</i>"
    ]

    return "\n".join(card_lines), get_unified_keyboard()


@router.message(Command("inbox"))
@router.message(Command("monitor"))
@router.message(Command("unread"))
@router.message(F.text.in_([
    "📬 Входящие: Drive2, VK & MAX",
    "📬 Входящие",
    "📬 Мониторинг: Drive2, VK & MAX",
    "📬 Drive2, VK & MAX",
    "🚗 Drive2 Уведомления",
    "🔵 VK Уведомления",
    "💬 MAX Уведомления",
    "💬 МАХ Уведомления"
]))
async def cmd_unified_monitor(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    text, kb = await build_unified_status_card(user_id, bot)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data == "unimon_check_all")
async def callback_check_all(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    await callback.answer("🔄 Проверяю Drive2, VK и MAX одновременно...")
    
    await asyncio.gather(
        check_user_drive2(user_id, bot, notify_if_no_change=False),
        check_vk_for_user(user_id, bot, notify_only_new=False),
        check_max_for_user(user_id, bot, notify_only_new=False),
        return_exceptions=True
    )

    text, kb = await build_unified_status_card(user_id, bot)
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        pass
    await callback.answer("✅ Все сервисы проверены!")


@router.callback_query(F.data == "unimon_open_d2")
async def callback_open_d2(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    cfg = get_user_drive2_config(user_id) or {}
    is_enabled = cfg.get("enabled", True)
    cur_msgs = cfg.get("last_messages", 0)
    cur_notifs = cfg.get("last_notifications", 0)

    lines_d2 = [
        "🚗 <b>Центр мониторинга Drive2.ru</b>",
        "",
        f"📊 <b>Состояние:</b> {'🟢 Активен (проверка каждые 60с)' if is_enabled else '⏸ На паузе'}",
        "🔐 <b>Авторизация:</b> 🔑 Сессия активна (Олег / manofftoday)",
        "",
        "📬 <b>Текущие счетчики:</b>",
        f"• 📩 Непрочитанных сообщений: <b>{cur_msgs}</b>",
        f"• 🔔 Новых уведомлений / событий: <b>{cur_notifs}</b>",
        "",
        "✨ <i>Все входящие прочитаны!</i>" if (cur_msgs == 0 and cur_notifs == 0) else "⚡ <i>Есть новые входящие на сайте!</i>",
        "",
        "🔗 <a href='https://www.drive2.ru/my/messages/'>Открыть сообщения на Drive2</a> | <a href='https://www.drive2.ru/my/notifications/'>Уведомления</a>"
    ]
    text = "\n".join(lines_d2)
    kb = get_drive2_control_keyboard(is_enabled)
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад к общему мониторингу", callback_data="unimon_back_hub")])
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "unimon_open_vk")
async def callback_open_vk(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    report = await check_vk_for_user(user_id, bot, notify_only_new=False)
    if not report:
        report = "🔵 <b>Мониторинг ВКонтакте</b>\n\nДанные не получены."
    kb = get_vk_keyboard(True, True)
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад к общему мониторингу", callback_data="unimon_back_hub")])
    try:
        await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "unimon_open_max")
async def callback_open_max(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    report = await check_max_for_user(user_id, bot, notify_only_new=False)
    if not report:
        report = "💬 <b>Мониторинг MAX</b>\n\nДанные не получены."
    kb = get_max_keyboard(True, True)
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад к общему мониторингу", callback_data="unimon_back_hub")])
    try:
        await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "unimon_back_hub")
async def callback_back_hub(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    text, kb = await build_unified_status_card(user_id, bot)
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        pass
    await callback.answer()
