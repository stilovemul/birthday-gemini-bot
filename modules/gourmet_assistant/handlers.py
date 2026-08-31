import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu
from core.states import SubTrackerStates
from modules.gourmet_assistant.breakfast import generate_express_breakfast
from modules.gourmet_assistant.barman import craft_cocktail

logger = logging.getLogger("GourmetHandlers")
router = Router(name="gourmet_assistant")


def get_gourmet_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍳 Быстрый завтрак (10 мин)", callback_data="gourmet_bf_quick"),
                InlineKeyboardButton(text="🥚 Завтрак из моих продуктов", callback_data="gourmet_bf_custom")
            ],
            [
                InlineKeyboardButton(text="🍸 Авторский коктейль", callback_data="gourmet_bar_cocktail"),
                InlineKeyboardButton(text="🍹 Безалкогольный моктейль", callback_data="gourmet_bar_mocktail")
            ]
        ]
    )


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

    return "\n".join(lines)


@router.message(Command("breakfast"))
@router.message(F.text.in_(["🍳 Экспресс-Завтраки", "🍳 Завтрак", "🍳 Завтраки"]))
async def cmd_breakfast(message: types.Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await generate_express_breakfast(user_id, ingredients="", mood="бодрый и энергичный")
    text = format_breakfast_message(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сгенерировать другой завтрак", callback_data="gourmet_bf_quick")],
            [InlineKeyboardButton(text="🍸 Перейти в AI-Бармен", callback_data="gourmet_bar_cocktail")]
        ]
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.message(Command("barman"))
@router.message(Command("cocktail"))
@router.message(F.text.in_(["🍸 AI-Бармен", "🍸 Бармен", "🍸 Коктейли"]))
async def cmd_barman(message: types.Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock="джин, виски, ром, тоник, сок, цитрусовые, мята, лед", non_alcoholic=False)
    text = format_cocktail_message(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Еще коктейль", callback_data="gourmet_bar_cocktail")],
            [InlineKeyboardButton(text="🍹 Безалкогольный", callback_data="gourmet_bar_mocktail")]
        ]
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "gourmet_bf_quick")
async def cb_bf_quick(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await generate_express_breakfast(user_id, mood="разнообразный и быстрый")
    text = format_breakfast_message(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сгенерировать другой", callback_data="gourmet_bf_quick")],
            [InlineKeyboardButton(text="🍸 AI-Бармен", callback_data="gourmet_bar_cocktail")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "gourmet_bar_cocktail")
async def cb_bar_cocktail(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock="", non_alcoholic=False)
    text = format_cocktail_message(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Еще коктейль", callback_data="gourmet_bar_cocktail")],
            [InlineKeyboardButton(text="🍹 Безалкогольный моктейль", callback_data="gourmet_bar_mocktail")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "gourmet_bar_mocktail")
async def cb_bar_mocktail(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    data = await craft_cocktail(user_id, bar_stock="сок, тоник, ягоды, мята, цитрусовые, лед", non_alcoholic=True)
    text = format_cocktail_message(data)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Еще безалкогольный", callback_data="gourmet_bar_mocktail")],
            [InlineKeyboardButton(text="🍸 Алкогольный коктейль", callback_data="gourmet_bar_cocktail")]
        ]
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()
