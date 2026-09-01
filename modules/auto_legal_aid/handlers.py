import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.auto_legal_aid.accident_guide import get_dtp_step_guide
from modules.auto_legal_aid.driver_rights import get_driver_legal_advice
from modules.auto_legal_aid.fine_disputer import generate_fine_appeal

logger = logging.getLogger("AutoLegalHandlers")
router = Router(name="auto_legal_aid")


def format_dtp_step(step_data: dict, current_step: int) -> tuple[str, InlineKeyboardMarkup]:
    lines = [
        f"<b>{step_data['title']}</b>\n",
        "\n".join(step_data["actions"]),
        f"\n{step_data['tip']}"
    ]
    
    buttons = []
    if current_step > 1:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"dtp_step_{current_step - 1}"))
    if current_step < 4:
        buttons.append(InlineKeyboardButton(text="Далее ➡️", callback_data=f"dtp_step_{current_step + 1}"))
    else:
        buttons.append(InlineKeyboardButton(text="🔄 С начала", callback_data="dtp_step_1"))

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [InlineKeyboardButton(text="⚖️ Оспорить штраф с камеры", callback_data="mode_start_fines")],
            [InlineKeyboardButton(text="👮‍♂️ Права водителя (КоАП)", callback_data="mode_start_rights")]
        ]
    )
    return "\n".join(lines), kb


@router.message(Command("dtp"))
@router.message(Command("rights"))
@router.message(F.text.in_(["🚗 Авто-Юрист", "🚗 Авто-Юрист & 🚨 ДТП", "Авто-Юрист", "🚨 Алгоритм при ДТП", "👮‍♂️ Шпаргалка водителя", "⚖️ Оспорить штраф"]))
async def cmd_auto_legal_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚨 Интерактивный гид ДТП", callback_data="mode_start_dtp")],
            [InlineKeyboardButton(text="👮‍♂️ Шпаргалка прав водителя", callback_data="mode_start_rights")],
            [InlineKeyboardButton(text="⚖️ Обжалование штрафа с камеры", callback_data="mode_start_fines")]
        ]
    )
    await message.answer(
        "🚗 <b>Авто-Юрист & 🚨 Помощник при ДТП:</b>\n\n"
        "Выберите раздел юридической помощи:\n"
        "• <b>Алгоритм при ДТП</b> — пошаговые инструкции, фотофиксация, Европротокол до 400 000 ₽.\n"
        "• <b>Права водителя</b> — статьи закона при остановке ДПС, осмотр vs досмотр, видеосъемка.\n"
        "• <b>Оспаривание штрафов</b> — анализ ошибок камер и генерация жалобы.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@router.callback_query(F.data == "mode_start_dtp")
async def cb_start_dtp(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.dtp_mode)
    data = get_dtp_step_guide(1)
    text, kb = format_dtp_step(data, 1)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("ДТП Ассистент"))
    await callback.answer()


@router.callback_query(F.data.startswith("dtp_step_"))
async def cb_dtp_step(callback: types.CallbackQuery):
    step_num = int(callback.data.replace("dtp_step_", ""))
    data = get_dtp_step_guide(step_num)
    text, kb = format_dtp_step(data, step_num)
    try:
        await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "mode_start_rights")
async def cb_start_rights(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.rights_mode)
    user_id = callback.from_user.id
    advice = await get_driver_legal_advice(user_id, "Остановка инспектором ДПС вне стационарного поста")
    lines = [
        "👮‍♂️ <b>Режим «Права водителя» активен:</b>\n",
        f"⚖️ <b>Статьи:</b> <code>{advice.get('legal_basis')}</code>\n",
        f"💬 <b>Что сказать:</b>\n<i>{advice.get('what_to_say')}</i>\n",
        f"⛔️ <b>Чего НЕ делать:</b>\n{advice.get('what_not_to_do')}\n",
        "\n💬 <i>Задайте любой вопрос по ПДД, КоАП или опишите вашу ситуацию:</i>"
    ]
    await callback.message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Права водителя"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_fines")
async def cb_start_fines(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.fine_dispute_mode)
    text = (
        "⚖️ <b>Режим «Оспаривание штрафов с камер» активен:</b>\n\n"
        "Опишите обстоятельства штрафа:\n"
        "👉 <i>«Штраф за сплошную, но на фото тень от авто пересекла линию»</i>\n"
        "👉 <i>«Штраф за скорость, но машина уже была продана по ДКП»</i>\n\n"
        "💡 <i>Бот оценит шансы и составит текст жалобы для ЦАФАП / Госуслуг.</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Оспаривание штрафа"))
    await callback.answer()


@router.message(ActiveModeStates.dtp_mode)
@router.message(ActiveModeStates.rights_mode)
@router.message(ActiveModeStates.fine_dispute_mode)
async def handle_auto_legal_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Авто-Юрист» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    curr_state = await state.get_state()

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    if curr_state == ActiveModeStates.fine_dispute_mode:
        appeal = await generate_fine_appeal(user_id, text)
        lines = [
            f"⚖️ <b>Обжалование штрафа:</b>\n",
            f"📊 Шансы на отмену: <b>{appeal.get('chances_percent')}%</b> | Срок: <b>{appeal.get('deadline_days')} суток</b>",
            f"🏛 Куда подавать: <i>{appeal.get('appeal_destination')}</i>\n",
            f"📑 Основание: <i>{appeal.get('grounds')}</i>\n",
            f"📝 <b>Текст жалобы:</b>\n<code>{appeal.get('appeal_text')}</code>\n",
            f"💡 <i>{appeal.get('step_instruction')}</i>"
        ]
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Авто-Юрист"))
    else:
        advice = await get_driver_legal_advice(user_id, text)
        lines = [
            f"👮‍♂️ <b>Разбор ситуации: {advice.get('title')}</b>\n",
            f"⚖️ <b>Закон:</b> <code>{advice.get('legal_basis')}</code>\n",
            f"💬 <b>Что сказать:</b>\n<i>{advice.get('what_to_say')}</i>\n",
            f"⛔️ <b>Запрещено:</b>\n{advice.get('what_not_to_do')}\n",
            f"📌 <b>Итог:</b> {advice.get('fine_or_penalty')}\n\n",
            "💬 <i>Можете задать уточняющий вопрос:</i>"
        ]
        await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Авто-Юрист"))
