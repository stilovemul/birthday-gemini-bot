import html
import io
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.icebreakers.generator import generate_icebreakers, ICEBREAKER_MODES

logger = logging.getLogger("IcebreakersHandlers")
router = Router(name="icebreakers")


def get_icebreaker_keyboard(current_cat: str = "dating") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💘 Дейтинг" + (" ✅" if current_cat == "dating" else ""), callback_data="ib_set_dating"),
                InlineKeyboardButton(text="💼 Нетворкинг" + (" ✅" if current_cat == "networking" else ""), callback_data="ib_set_networking")
            ],
            [
                InlineKeyboardButton(text="🔥 Оживить диалог" + (" ✅" if current_cat == "revive" else ""), callback_data="ib_set_revive"),
                InlineKeyboardButton(text="🎭 Креатив" + (" ✅" if current_cat == "creative" else ""), callback_data="ib_set_creative")
            ],
            [
                InlineKeyboardButton(text="💬 Новый заход", callback_data="ib_new_query"),
                InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("icebreaker"))
@router.message(Command("dating"))
@router.message(F.text.in_(["💬 Знакомства", "💬 Ice-Breakers", "💬 Генератор Ice-Breakers", "Знакомства", "Ice-Breakers"]))
async def cmd_icebreakers(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.icebreakers_mode)
    await state.update_data(category="dating")
    
    text = (
        "💬 <b>Генератор Ice-Breakers для знакомств & нетворкинга:</b>\n\n"
        "Забудьте про скучные <i>«Привет, как дела?»</i> и неловкие паузы!\n\n"
        "📸 <b>Как использовать:</b>\n"
        "• Отправьте <b>СКРИНШОТ / ФОТО профиля</b> из Tinder/VK/Telegram.\n"
        "• Или напишите текстом: описание человека, увлечения или ситуацию.\n\n"
        "🎯 <b>Текущий режим:</b> 💘 <b>Дейтинг & Знакомства</b>\n"
        "💡 Я выдам 4 остроумных, цепляющих первых фразы под конкретную ситуацию!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_icebreaker_keyboard("dating"))


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_icebreakers(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏁 <b>Режим «Знакомства & Нетворкинг» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )
    await callback.answer("Вы вышли в главное меню")


@router.callback_query(F.data.startswith("ib_set_"))
async def cb_set_icebreaker_cat(callback: types.CallbackQuery, state: FSMContext):
    cat_key = callback.data.replace("ib_set_", "")
    await state.set_state(ActiveModeStates.icebreakers_mode)
    await state.update_data(category=cat_key)
    
    cat_info = ICEBREAKER_MODES.get(cat_key, ICEBREAKER_MODES["dating"])
    await callback.message.edit_text(
        f"🎯 <b>Выбран режим:</b> {cat_info['title']}\n"
        f"📝 <i>{cat_info['description']}</i>\n\n"
        "💬 <b>Пришлите скриншот/фото профиля или опишите детали человека:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_icebreaker_keyboard(cat_key)
    )
    await callback.answer(f"Режим: {cat_info['title']}")


@router.callback_query(F.data == "ib_new_query")
async def cb_ib_new(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.icebreakers_mode)
    await callback.message.answer(
        "💬 <b>Отправьте новые данные (фото или описание профиля):</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.icebreakers_mode, F.photo)
async def handle_icebreaker_photo(message: types.Message, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await state.get_data()
    cat = data.get("category", "dating")

    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_bytes_io = await message.bot.download_file(file_info.file_path)
    image_bytes = file_bytes_io.read()

    result = await generate_icebreakers(message.from_user.id, context="Фото профиля", category=cat, image_bytes=image_bytes)
    await _send_icebreaker_result(message, result, cat)


@router.message(ActiveModeStates.icebreakers_mode, F.text)
async def handle_icebreaker_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Знакомства & Нетворкинг» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await state.get_data()
    cat = data.get("category", "dating")

    result = await generate_icebreakers(message.from_user.id, context=raw_text, category=cat)
    await _send_icebreaker_result(message, result, cat)


async def _send_icebreaker_result(message: types.Message, result: dict, cat: str):
    cat_title = html.escape(str(result.get("category_title", "Знакомства")))
    insight = html.escape(str(result.get("profile_insight", "")))
    items = result.get("icebreakers", [])

    lines = [
        f"🎯 <b>ТОП ICE-BREAKERS ({cat_title}):</b>\n",
        f"💡 <b>Крючок профиля:</b> <i>{insight}</i>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, ib in enumerate(items, 1):
        line = html.escape(str(ib.get("line", "")))
        style = html.escape(str(ib.get("style", "Остроумный")))
        why = html.escape(str(ib.get("why_it_works", "")))
        followup = html.escape(str(ib.get("followup_hook", "")))

        lines.append(
            f"<b>{idx}. [{style}]</b>\n"
            f"<code>{line}</code>\n"
            f"  └ 🧠 <i>Почему сработает: {why}</i>\n"
            f"  └ 🚀 <i>Следующий ход: {followup}</i>\n"
        )

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_icebreaker_keyboard(cat))
