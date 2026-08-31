import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.gourmet_assistant.breakfast import generate_express_breakfast
from modules.gourmet_assistant.barman import craft_cocktail

logger = logging.getLogger("GourmetHandlers")
router = Router(name="gourmet_assistant")


def format_breakfast_message(data: dict) -> str:
    lines = [
        f"🍳 <b>{data.get('title', 'Экспресс-завтрак')}</b>",
        f"⏱ Время: <b>{data.get('prep_time', '10 мин')}</b> | ⚡️ КБЖУ: <b>{data.get('calories', 400)} ккал</b> (Б: {data.get('protein', 20)}г | Ж: {data.get('fats', 15)}г | У: {data.get('carbs', 25)}г)\n",
        "🛒 <b>Ингредиенты:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")

    lines.append("\n👨‍🍳 <b>Приготовление:</b>")
    for step in data.get("steps", []):
        lines.append(f"  {step}")

    if data.get("chef_tip"):
        lines.append(f"\n{data['chef_tip']}")

    lines.append("\n💬 <i>Напишите пожелания (например: «без яиц», «больше белка», «из творога») или примените кнопку ниже:</i>")
    return "\n".join(lines)


def format_cocktail_message(data: dict) -> str:
    lines = [
        f"🍸 <b>{data.get('title', 'Коктейль')}</b>",
        f"🏷 Стиль: <i>{data.get('category', 'Классика')}</i> | Крепость: <b>{data.get('strength', '12%')}</b>",
        f"🥃 Бокал: <i>{data.get('glassware', 'Хайбол со льдом')}</i>\n",
        "🧊 <b>Состав и пропорции:</b>"
    ]
    for ing in data.get("ingredients", []):
        lines.append(f"  • {ing}")

    lines.append("\n🍹 <b>Метод приготовления:</b>")
    for step in data.get("recipe_steps", []):
        lines.append(f"  {step}")

    if data.get("barman_secret"):
        lines.append(f"\n{data['barman_secret']}")

    lines.append("\n💬 <i>Напишите ваши напитки или пожелание (например: «хочу покислее», «добавь виски»):</i>")
    return "\n".join(lines)


@router.message(Command("breakfast"))
@router.message(Command("barman"))
@router.message(F.text.in_(["🍳 Завтрак & 🍸 Бармен", "🍳 Экспресс-Завтраки", "🍸 AI-Бармен"]))
async def cmd_gourmet_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍳 Режим: Экспресс-Завтрак (10 мин)", callback_data="mode_start_breakfast")],
            [InlineKeyboardButton(text="🍸 Режим: AI-Бармен & Коктейли", callback_data="mode_start_barman")]
        ]
    )
    await message.answer(
        "🍳 <b>Кулинарный шеф & 🍸 AI-Бармен:</b>\n\n"
        "Выберите режим работы:\n"
        "• <b>Завтраки за 10 минут</b> — сытные сбалансированные блюда с расчетом КБЖУ.\n"
        "• <b>AI-Бармен</b> — авторские коктейли и моктейли по напиткам из вашего бара.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@router.callback_query(F.data == "mode_start_breakfast")
async def cb_start_breakfast(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.breakfast_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await generate_express_breakfast(user_id, ingredients="", mood="бодрый и сытный")
    text = format_breakfast_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Завтрак"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_barman")
async def cb_start_barman(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.barman_mode)
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock="джин, виски, ром, тоник, сок, цитрусовые, мята, лед", non_alcoholic=False)
    text = format_cocktail_message(data)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("AI-Бармен"))
    await callback.answer()


@router.message(ActiveModeStates.breakfast_mode)
async def handle_breakfast_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Завтрак» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await generate_express_breakfast(user_id, ingredients=text, mood="по запросу пользователя")
    reply = format_breakfast_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Завтрак"))


@router.message(ActiveModeStates.barman_mode)
async def handle_barman_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «AI-Бармен» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    is_non_alcol = "безалк" in text.lower() or "моктейл" in text.lower()
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock=text, non_alcoholic=is_non_alcol)
    reply = format_cocktail_message(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("AI-Бармен"))
