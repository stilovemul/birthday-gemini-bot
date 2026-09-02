import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.gift_generator.generator import generate_gift_ideas
from modules.birthdays.storage import get_sorted_birthdays

logger = logging.getLogger("GiftGeneratorHandlers")
router = Router(name="gift_generator")


def get_gift_keyboard() -> InlineKeyboardMarkup:
    birthdays = get_sorted_birthdays()
    buttons = []
    row = []
    for b in birthdays[:6]:
        name = b.get("name", "Именинник")
        row.append(InlineKeyboardButton(text=f"🎁 {name}", callback_data=f"gift_b_{name}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🎲 Универсальные вау-подарки", callback_data="gift_preset_universal"),
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("gift"))
@router.message(Command("gifts"))
@router.message(F.text.in_(["🎁 Подарки", "Подарки", "Генератор подарков", "Идеи подарков"]))
async def cmd_gift_generator(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.gift_generator_mode)
    text = (
        "🎁 <b>AI-Генератор Подарков & Впечатлений:</b>\n\n"
        "Я подбираю <b>небанальные подарки и эмоции</b> под характер, возраст и бюджет человека!\n\n"
        "💡 <b>Как пользоваться:</b>\n"
        "1. 🔘 <b>Нажмите на имя человека из вашей базы дней рождения</b> на кнопках ниже.\n"
        "2. ✍️ <b>Или напишите произвольно:</b> <i>«Подарок жене на 30 лет, бюджет 15 000 ₽, любит уют и путешествия»</i>, <i>«Что подарить другу-автомобилисту до 5 000 ₽»</i>."
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Подарки"))
    await message.answer("👇 <b>Выберите человека или напишите запрос:</b>", parse_mode=ParseMode.HTML, reply_markup=get_gift_keyboard())


@router.callback_query(F.data.startswith("gift_"))
async def cb_gift_preset(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.gift_generator_mode)
    data = callback.data.replace("gift_", "")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    if data.startswith("b_"):
        person_name = data.replace("b_", "")
        q = f"Оригинальный подарок на день рождения для {person_name} из моего списка близких"
    else:
        q = "Топ-5 универсальных подарков и сертификатов на впечатления с вау-эффектом"

    await callback.answer("Подбираю идеи подарков...")
    res = await generate_gift_ideas(callback.from_user.id, q)
    await render_gift_results(callback.message, res)


@router.message(ActiveModeStates.gift_generator_mode, F.text)
async def handle_gift_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Генератор подарков» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await generate_gift_ideas(message.from_user.id, raw_text)
    await render_gift_results(message, res)


async def render_gift_results(message: types.Message, res: dict):
    summary = html.escape(str(res.get("recipient_summary", "Идеи подарков")))
    gifts = res.get("gifts", [])
    presentation = html.escape(str(res.get("presentation_idea", "")))

    lines = [
        f"🎁 <b>ПОДБОРКА ПОДАРКОВ & ВПЕЧАТЛЕНИЙ:</b>\n",
        f"🎯 <b>Концепция:</b> <i>{summary}</i>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, g in enumerate(gifts, 1):
        title = html.escape(str(g.get("title", "Подарок")))
        cat = html.escape(str(g.get("category", "")))
        price = html.escape(str(g.get("price_est", "")))
        why = html.escape(str(g.get("why_awesome", "")))
        where = html.escape(str(g.get("where_to_buy", "")))

        lines.append(
            f"<b>{idx}. 🎀 {title}</b> <i>({cat})</i>\n"
            f"   💰 <b>Бюджет:</b> {price}\n"
            f"   ✨ <b>Почему супер:</b> <i>{why}</i>\n"
            f"   🛒 <b>Где купить:</b> <code>{where}</code>\n"
        )

    if presentation:
        lines.append(f"🎉 <b>Идея эффектного вручения:</b>\n<i>{presentation}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_gift_keyboard())
