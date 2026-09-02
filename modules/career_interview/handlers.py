import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.career_interview.sparring import conduct_interview_turn

logger = logging.getLogger("CareerInterviewHandlers")
router = Router(name="career_interview")


def get_interview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👔 Руководитель / Team Lead", callback_data="int_role_lead"),
                InlineKeyboardButton(text="💻 IT / Senior Разработчик", callback_data="int_role_it")
            ],
            [
                InlineKeyboardButton(text="📈 Продажи / Переговоры", callback_data="int_role_sales"),
                InlineKeyboardButton(text="🎯 Торг о повышении зарплаты", callback_data="int_role_salary")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("interview"))
@router.message(F.text.in_(["🎙 Собеседование", "Собеседование", "Карьерный спарринг", "Тренажер интервью"]))
async def cmd_interview(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.career_interview_mode)
    await state.update_data(interview_history="")
    text = (
        "🎙 <b>AI-Собеседование & Карьерный спарринг:</b>\n\n"
        "Я моделирую **реальное жесткое собеседование** на любую должность: задаю каверзные вопросы, оцениваю ваши ответы и учу забирать оффер на максимальных условиях!\n\n"
        "💡 <b>Как тренироваться:</b>\n"
        "1. Напишите желаемую должность или ситуацию: <i>«Хочу пройти собеседование на должность руководителя проектов»</i>.\n"
        "2. Отвечайте текстом или **голосом 🎙** — я разберу каждый ответ!\n"
        "3. Или выберите роль на кнопках ниже."
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Собеседование"))
    await message.answer("👇 <b>Выберите направление тренировки:</b>", reply_markup=get_interview_keyboard())


@router.callback_query(F.data.startswith("int_role_"))
async def cb_interview_role(callback: types.CallbackQuery, state: FSMContext):
    role_key = callback.data.replace("int_role_", "")
    await state.set_state(ActiveModeStates.career_interview_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    roles = {
        "lead": "Собеседование на позицию Руководителя отдела / Team Lead",
        "it": "Собеседование на Senior IT специалиста / Архитектора",
        "sales": "Собеседование на топового менеджера по сложным B2B продажам",
        "salary": "Переговоры с генеральным директором о повышении зарплаты на 30%"
    }
    r = roles.get(role_key, "Собеседование")
    await state.update_data(interview_history=f"Роль: {r}")
    await callback.answer("Начинаем симуляцию собеседования...")
    res = await conduct_interview_turn(callback.from_user.id, f"Начинаем: {r}")
    await render_interview_turn(callback.message, res)


@router.message(ActiveModeStates.career_interview_mode, F.text)
async def handle_interview_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Собеседование» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    data = await state.get_data()
    hist = data.get("interview_history", "")
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await conduct_interview_turn(message.from_user.id, raw_text, history=hist)
    
    # Update history
    new_hist = f"{hist}\nКандидат: {raw_text}\nИнтервьюер: {res.get('next_tough_question', '')}"
    await state.update_data(interview_history=new_hist[-1500:])
    await render_interview_turn(message, res)


async def render_interview_turn(message: types.Message, res: dict):
    feedback = html.escape(str(res.get("feedback_on_previous", "")))
    reaction = html.escape(str(res.get("interviewer_reaction", "")))
    question = html.escape(str(res.get("next_tough_question", "")))
    tip = html.escape(str(res.get("pro_tip", "")))

    lines = []
    if feedback:
        lines.append(f"📊 <b>Разбор вашего ответа:</b>\n{feedback}\n")

    lines.append(f"👔 <b>Интервьюер:</b> <i>«{reaction}»</i>\n")
    lines.append(f"❓ <b>ВОПРОС КАНДИДАТУ:</b>\n<b>{question}</b>\n")
    
    if tip:
        lines.append(f"💡 <b>Подсказка эксперта:</b>\n<i>{tip}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_interview_keyboard())
