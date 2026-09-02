import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.dark_kitchen.chef import cook_from_fridge_leftovers

logger = logging.getLogger("DarkKitchenHandlers")
router = Router(name="dark_kitchen")


def get_dark_kitchen_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍳 Экспресс-Ужин за 15 мин", callback_data="dk_quick"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("darkkitchen"))
@router.message(Command("leftovers"))
@router.message(F.text.in_(["👨‍🍳 Ужин из холодильника", "Ужин из холодильника", "Шеф из остатков", "Что приготовить"]))
async def cmd_dark_kitchen(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.dark_kitchen_mode)
    text = (
        "👨‍🍳 <b>Ресторанный ужин из остатков холодильника:</b>\n\n"
        "Назовите **любые 3–5 случайных продуктов**, которые есть дома — и я превращу их в **шедевр ресторанного уровня за 15 минут** с секретным соусом и правильной подачей!\n\n"
        "💡 <b>Примеры:</b>\n"
        "• <i>«Банка тунца, спагетти, сливки и лук»</i>\n"
        "• <i>«Куриное филе, яйца, соевый соус, рис и замороженные овощи»</i>\n"
        "• <i>«Фарш, картошка, сыр и пол-помидора»</i>\n\n"
        "💬 <i>Напишите, что у вас есть в холодильнике:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Ужин из холодильника"))


@router.callback_query(F.data == "dk_quick")
async def cb_dk_quick(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.dark_kitchen_mode)
    await callback.message.answer("💬 <b>Напишите продукты через запятую:</b>", parse_mode=ParseMode.HTML)
    await callback.answer()


@router.message(ActiveModeStates.dark_kitchen_mode, F.text)
async def handle_dark_kitchen_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Ужин из холодильника» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await cook_from_fridge_leftovers(message.from_user.id, raw_text)
    await render_dark_kitchen_results(message, res)


async def render_dark_kitchen_results(message: types.Message, res: dict):
    dish = html.escape(str(res.get("dish_name", "Ресторанное блюдо")))
    time_est = html.escape(str(res.get("prep_time", "15 минут")))
    diff = html.escape(str(res.get("difficulty", "Легко")))
    sauce = html.escape(str(res.get("secret_sauce", "")))
    steps = res.get("cooking_steps", [])
    hack = html.escape(str(res.get("chef_hack", "")))
    pres = html.escape(str(res.get("presentation", "")))

    lines = [
        f"👨‍🍳 <b>{dish.upper()}</b>\n",
        f"⏱ <b>Время:</b> {time_est} | 📊 <b>Сложность:</b> {diff}\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    if sauce:
        lines.append(f"🧪 <b>Секретный соус / эмульсия:</b>\n<i>{sauce}</i>\n")

    lines.append("📋 <b>ПОШАГОВОЕ ПРИГОТОВЛЕНИЕ:</b>")
    for s in steps:
        lines.append(f"{html.escape(str(s))}")
    lines.append("")

    if hack:
        lines.append(f"🔥 <b>Лайфхак шеф-повара:</b>\n<i>{hack}</i>\n")

    if pres:
        lines.append(f"🍽 <b>Подача:</b> {pres}")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_dark_kitchen_keyboard())
