import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
            [InlineKeyboardButton(text="⚖️ Оспорить штраф", callback_data="fine_dispute_start")],
            [InlineKeyboardButton(text="👮‍♂️ Шпаргалка ПДД", callback_data="rights_quick_faq")]
        ]
    )
    return "\n".join(lines), kb


@router.message(Command("dtp"))
@router.message(F.text.in_(["🚨 Алгоритм при ДТП", "🚨 ДТП", "🚨 Авария"]))
async def cmd_dtp(message: types.Message):
    data = get_dtp_step_guide(1)
    text, kb = format_dtp_step(data, 1)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


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


@router.message(Command("rights"))
@router.message(F.text.in_(["👮‍♂️ Шпаргалка водителя", "👮‍♂️ Права водителя", "👮‍♂️ КоАП"]))
async def cmd_rights(message: types.Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    advice = await get_driver_legal_advice(user_id, "Инспектор ДПС остановил вне стационарного поста и требует открыть багажник")
    
    lines = [
        f"👮‍♂️ <b>{advice.get('title')}</b>\n",
        f"⚖️ <b>Правовая база:</b> <code>{advice.get('legal_basis')}</code>\n",
        f"💬 <b>Что сказать инспектору:</b>\n<i>{advice.get('what_to_say')}</i>\n",
        f"⛔️ <b>Чего НЕ делать:</b>\n{advice.get('what_not_to_do')}\n",
        f"📌 <b>Итог:</b> {advice.get('fine_or_penalty')}"
    ]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Осмотр vs Досмотр багажника", callback_data="rights_faq_bagazh")],
            [InlineKeyboardButton(text="📱 Съемка инспектора на видео", callback_data="rights_faq_video")],
            [InlineKeyboardButton(text="🚨 Алгоритм при ДТП", callback_data="dtp_step_1")]
        ]
    )
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "rights_faq_bagazh")
async def cb_rights_bagazh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    advice = await get_driver_legal_advice(user_id, "Разница между визуальным осмотром и досмотром автомобиля. Требование понятых или видеозаписи по ст. 27.9 КоАП")
    lines = [
        f"👮‍♂️ <b>{advice.get('title')}</b>\n",
        f"⚖️ <b>Закон:</b> <code>{advice.get('legal_basis')}</code>\n",
        f"💬 <b>Формулировка:</b>\n<i>{advice.get('what_to_say')}</i>\n",
        f"⛔️ <b>Запрещено:</b>\n{advice.get('what_not_to_do')}\n",
        f"📌 <b>Итог:</b> {advice.get('fine_or_penalty')}"
    ]
    await callback.message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "rights_faq_video")
async def cb_rights_video(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    advice = await get_driver_legal_advice(user_id, "Право водителя вести видеосъемку инспектора ГИБДД на телефон согласно ст. 8 ФЗ 'О полиции' (принцип гласности и открытости)")
    lines = [
        f"👮‍♂️ <b>{advice.get('title')}</b>\n",
        f"⚖️ <b>Закон:</b> <code>{advice.get('legal_basis')}</code>\n",
        f"💬 <b>Формулировка:</b>\n<i>{advice.get('what_to_say')}</i>\n",
        f"⛔️ <b>Запрещено:</b>\n{advice.get('what_not_to_do')}\n",
        f"📌 <b>Итог:</b> {advice.get('fine_or_penalty')}"
    ]
    await callback.message.answer("\n".join(lines), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.message(Command("fine_dispute"))
@router.message(F.text.in_(["⚖️ Оспорить штраф", "⚖️ Штрафы", "⚖️ Обжалование штрафа"]))
async def cmd_fine_dispute(message: types.Message):
    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    appeal = await generate_fine_appeal(user_id, "Штраф с камеры за пересечение сплошной линии 500 руб, но на фото видно, что линию пересекла тень от машины в солнечный день")
    
    lines = [
        f"⚖️ <b>Обжалование штрафа с камеры ({appeal.get('violation_type')})</b>\n",
        f"📊 <b>Шансы на отмену:</b> <b>{appeal.get('chances_percent')}%</b>",
        f"⏳ <b>Срок на подачу:</b> <b>{appeal.get('deadline_days')} суток</b> с момента получения\n",
        f"🏛 <b>Куда подавать:</b> <i>{appeal.get('appeal_destination')}</i>",
        f"📑 <b>Юридическое основание:</b> <i>{appeal.get('grounds')}</i>\n",
        f"📝 <b>Текст жалобы:</b>\n<code>{appeal.get('appeal_text')}</code>\n",
        f"💡 <i>{appeal.get('step_instruction')}</i>"
    ]
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚨 Алгоритм при ДТП", callback_data="dtp_step_1")],
            [InlineKeyboardButton(text="👮‍♂️ Права водителя", callback_data="rights_quick_faq")]
        ]
    )
    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "fine_dispute_start")
async def cb_fine_dispute_start(callback: types.CallbackQuery):
    await cmd_fine_dispute(callback.message)
    await callback.answer()


@router.callback_query(F.data == "rights_quick_faq")
async def cb_rights_quick_faq(callback: types.CallbackQuery):
    await cmd_rights(callback.message)
    await callback.answer()
