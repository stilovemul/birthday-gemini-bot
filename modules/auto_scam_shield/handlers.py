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
from modules.auto_scam_shield.analyzer import analyze_repair_estimate

logger = logging.getLogger("AutoScamShieldHandlers")
router = Router(name="auto_scam_shield")


def get_scam_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Сфотографировать заказ-наряд", callback_data="scam_hint_photo"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("autocheck"))
@router.message(Command("autoservice"))
@router.message(F.text.in_(["🛡 Анти-Развод Авто", "Анти-Развод", "Анти-Развод Автосервис", "Проверка заказ-наряда"]))
async def cmd_auto_scam_shield(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.auto_scam_shield_mode)
    text = (
        "🛡 <b>Анти-Развод в Автосервисе & Экспертиза смет:</b>\n\n"
        "Я проверяю заказ-наряды и сметы ремонтов: **выявляю навязанные услуги, защищаю от переплат и рассчитываю честную цену по рынку СПб**!\n\n"
        "💡 <b>Как проверить смету:</b>\n"
        "1. 📸 <b>Сфотографируйте заказ-наряд или чек</b> и отправьте сюда фото!\n"
        "2. ✍️ <b>Или скопируйте текст/список работ:</b> <i>«Замена масла 2500р, промывка форсунок 6000р, очистка суппортов 3500р, замена колодок 4000р»</i>.\n\n"
        "💬 <i>Отправьте фото или текст сметы:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Анти-Развод Авто"))


@router.callback_query(F.data == "scam_hint_photo")
async def cb_scam_photo_hint(callback: types.CallbackQuery):
    await callback.message.answer("📸 <b>Сделайте четкое фото заказ-наряда или счета и отправьте его сюда сообщением!</b>", parse_mode=ParseMode.HTML)
    await callback.answer()


@router.message(ActiveModeStates.auto_scam_shield_mode, F.photo)
async def handle_scam_photo(message: types.Message, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    photo = message.photo[-1]
    file_io = io.BytesIO()
    await message.bot.download(photo, destination=file_io)
    img_bytes = file_io.getvalue()

    caption = message.caption or "Анализ фото заказ-наряда автосервиса"
    res = await analyze_repair_estimate(message.from_user.id, caption, image_bytes=img_bytes)
    await render_scam_results(message, res)


@router.message(ActiveModeStates.auto_scam_shield_mode, F.text)
async def handle_scam_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Анти-Развод Авто» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await analyze_repair_estimate(message.from_user.id, raw_text)
    await render_scam_results(message, res)


async def render_scam_results(message: types.Message, res: dict):
    verdict = html.escape(str(res.get("overall_verdict", "Аудит сметы")))
    scam_items = res.get("scam_items", [])
    critical = res.get("critical_items", [])
    fair_price = html.escape(str(res.get("fair_price_estimate", "")))
    script = html.escape(str(res.get("negotiation_script", "")))

    lines = [
        f"🛡 <b>РЕЗУЛЬТАТ ЭКСПЕРТИЗЫ СМЕТЫ:</b>\n",
        f"📊 <b>Вердикт:</b> <b>{verdict}</b>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    if scam_items:
        lines.append("❌ <b>НАВЯЗАННЫЕ ПОЗИЦИИ (ВЫЧЕРКНУТЬ):</b>")
        for s in scam_items:
            item = html.escape(str(s.get("item", "")))
            price = html.escape(str(s.get("price_in_bill", "")))
            why = html.escape(str(s.get("why_scam", "")))
            lines.append(f"• <b>{item}</b> ({price})\n  └ ⚠️ <i>{why}</i>")
        lines.append("")

    if critical:
        lines.append("✅ <b>ДЕЙСТВИТЕЛЬНО ВАЖНЫЕ РАБОТЫ:</b>")
        for c in critical:
            lines.append(f"• {html.escape(str(c))}")
        lines.append("")

    if fair_price:
        lines.append(f"💰 <b>Справедливая цена по рынку:</b>\n{fair_price}\n")

    if script:
        lines.append(f"🗣 <b>Что сказать мастеру-приемщику:</b>\n{script}")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_scam_keyboard())
