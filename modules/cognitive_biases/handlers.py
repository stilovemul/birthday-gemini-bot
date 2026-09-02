import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.cognitive_biases.analyzer import analyze_cognitive_biases

logger = logging.getLogger("CognitiveBiasesHandlers")
router = Router(name="cognitive_biases")


def get_biases_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 Разобрать ещё ситуацию", callback_data="cb_new_bias_analysis"),
                InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("biases"))
@router.message(Command("thinking"))
@router.message(F.text.in_(["🧠 Мышление", "🧠 Когнитивные искажения", "🧠 Разбор искажений", "Когнитивные искажения", "Мышление"]))
async def cmd_cognitive_biases(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.cognitive_biases_mode)
    text = (
        "🧠 <b>Разбор когнитивных искажений & Аудит рациональности:</b>\n\n"
        "Наш мозг ежедневно попадает в сотни эволюционных ловушек (ошибка невозвратных затрат, иллюзия контроля, ошибка выжившего, предвзятость подтверждения).\n\n"
        "🔍 <b>Опишите вашу дилемму, спор, тревогу или решение:</b>\n"
        "• <i>«Не могу бросить проект, в который вложил год, хотя он не приносит денег»</i>\n"
        "• <i>«Кажется, что коллега специально ставит палки в колеса»</i>\n"
        "• <i>«Боюсь начать новое дело, потому что все вокруг уже успешны»</i>\n\n"
        "💡 Я разберу искажения и дам <b>трезвый рациональный чек-лист</b> для идеального решения!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Мышление & Логика"))


@router.callback_query(F.data == "cb_new_bias_analysis")
async def cb_biases_new(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cognitive_biases_mode)
    await callback.message.answer(
        "💬 <b>Опишите новую ситуацию или сомнение для разбора мышления:</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.cognitive_biases_mode, F.text)
async def handle_biases_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if raw_text.startswith("/") or raw_text in ["🚪 Главное меню", "Главное меню", "Выход"]:
        await state.clear()
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    result = await analyze_cognitive_biases(message.from_user.id, raw_text)

    biases = result.get("detected_biases", [])
    bias_lines = []
    for idx, b in enumerate(biases, 1):
        b_name = html.escape(str(b.get("name", "Искажение")))
        b_desc = html.escape(str(b.get("description", "")))
        bias_lines.append(f"<b>{idx}. 🪤 {b_name}</b>\n   └ <i>{b_desc}</i>")

    biases_str = "\n\n".join(bias_lines) if bias_lines else "Искажение восприятия"
    explanation = html.escape(str(result.get("brain_trap_explanation", "")))
    checklist = result.get("rational_checklist", [])
    check_str = "\n".join(f"  • ❓ <i>{html.escape(str(q))}</i>" for q in checklist)
    step = html.escape(str(result.get("optimal_rational_step", "")))

    card = (
        "🧠 <b>АУДИТ МЫШЛЕНИЯ И КОГНИТИВНЫХ ЛОВУШЕК:</b>\n\n"
        f"{biases_str}\n\n"
        f"🔬 <b>Анатомия самообмана:</b>\n<i>{explanation}</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>РАЦИОНАЛЬНЫЙ ЧЕК-ЛИСТ ДЛЯ РЕШЕНИЯ:</b>\n{check_str}\n\n"
        f"🎯 <b>Оптимальный трезвый шаг:</b>\n<b>{step}</b>"
    )

    await message.answer(card, parse_mode=ParseMode.HTML, reply_markup=get_biases_keyboard())
