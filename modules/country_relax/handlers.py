import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.country_relax.finder import find_country_resorts

logger = logging.getLogger("CountryRelaxHandlers")
router = Router(name="country_relax")


def get_country_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏊‍♂️ Бассейн с подогревом & Спа", callback_data="cr_pool"),
                InlineKeyboardButton(text="🪵 Русская баня на дровах у озера", callback_data="cr_banya")
            ],
            [
                InlineKeyboardButton(text="🏕 Стильный глэмпинг в лесу", callback_data="cr_glamp"),
                InlineKeyboardButton(text="👨‍👩‍👧 Семейный коттедж с детьми", callback_data="cr_family")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("countryside"))
@router.message(Command("spa"))
@router.message(F.text.in_(["🏕 Загородный отдых", "Загородный отдых", "Бани & Спа", "Глэмпинг", "Коттеджи"]))
async def cmd_country_relax(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.country_relax_mode)
    text = (
        "🏕 <b>Загородный семейный отдых, Спа, Бани & Бассейны:</b>\n\n"
        "Интерактивный подбор загородных отелей, баз и коттеджей по СПб, Ленобласти и Карелии под ваши точные критерии!\n\n"
        "💡 <b>Напишите ваши пожелания, например:</b>\n"
        "• <i>«Хотим баню на дровах, мангал, до 10 000 руб/сутки у воды»</i>\n"
        "• <i>«Спа-отель с теплым открытым бассейном на выходные для двоих»</i>\n"
        "• <i>«Коттедж для семьи с ребенком 4 года, детской площадкой до 1 часа от СПб»</i>\n\n"
        "💬 <i>Напишите запрос или выберите готовую категорию:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Загородный отдых"))
    await message.answer("👇 <b>Быстрый подбор баз:</b>", reply_markup=get_country_keyboard())


@router.callback_query(F.data.startswith("cr_"))
async def cb_country_preset(callback: types.CallbackQuery, state: FSMContext):
    preset = callback.data.replace("cr_", "")
    await state.set_state(ActiveModeStates.country_relax_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    queries = {
        "pool": "Загородные отели Ленобласти с открытым подогреваемым бассейном круглый год и спа",
        "banya": "Базы отдыха на берегу озера с настоящей русской баней на дровах и мангальной зоной",
        "glamp": "Топ стильных глэмпингов и купольных домиков в лесу у воды в ЛО и Карелии",
        "family": "Семейные загородные клубы с детской комнатой, анимацией, площадкой и рестораном"
    }
    q = queries.get(preset, "Загородный отдых в Ленобласти")
    await callback.answer("Подбираю лучшие загородные базы...")
    res = await find_country_resorts(callback.from_user.id, q)
    await render_country_results(callback.message, res)


@router.message(ActiveModeStates.country_relax_mode, F.text)
async def handle_country_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Загородный отдых» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await find_country_resorts(message.from_user.id, raw_text)
    await render_country_results(message, res)


async def render_country_results(message: types.Message, res: dict):
    title = html.escape(str(res.get("title", "Загородный отдых")))
    resorts = res.get("resorts", [])
    tip = html.escape(str(res.get("booking_tip", "")))

    lines = [
        f"🏕 <b>{title.upper()}:</b>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, r in enumerate(resorts, 1):
        name = html.escape(str(r.get("name", "База отдыха")))
        loc = html.escape(str(r.get("location", "")))
        price = html.escape(str(r.get("price_range", "")))
        features = html.escape(str(r.get("features", "")))
        kids = html.escape(str(r.get("kid_rating", "")))
        why = html.escape(str(r.get("why_best", "")))

        lines.append(
            f"<b>{idx}. 🌲 {name}</b>\n"
            f"   📍 <b>Локация:</b> {loc}\n"
            f"   💰 <b>Цены:</b> {price}\n"
            f"   🪵 <b>Инфраструктура:</b> {features}\n"
            f"   👶 <b>Для детей:</b> {kids}\n"
            f"   🎯 <b>Почему стоит поехать:</b> <i>{why}</i>\n"
        )

    if tip:
        lines.append(f"💡 <b>Совет по бронированию:</b>\n<i>{tip}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_country_keyboard())
