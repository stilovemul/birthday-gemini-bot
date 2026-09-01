import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard
from core.states import ActiveModeStates
from modules.ai_deep_research.researcher import conduct_deep_research
from modules.ai_deep_research.fact_checker import verify_claim_or_news

logger = logging.getLogger("ResearchHandlers")
router = Router(name="ai_deep_research")


def format_research_card(data: dict) -> str:
    lines = [
        f"🔬 <b>{data.get('title')}</b>\n",
        f"💡 <b>Главный вывод (Summary):</b>\n<i>{data.get('executive_summary')}</i>\n",
        "📌 <b>Ключевые инсайты:</b>"
    ]
    for ins in data.get("key_insights", []):
        lines.append(f"  • {ins}")

    comp = data.get("comparison", [])
    if comp:
        lines.append("\n📊 <b>Сравнительный анализ вариантов:</b>")
        for it in comp:
            lines.append(
                f"  👉 <b>{it.get('name')}</b> (Рейтинг: <b>{it.get('score', '9/10')}</b>)\n"
                f"     + <i>{it.get('pros')}</i>\n"
                f"     - <i>{it.get('cons')}</i>"
            )

    if data.get("verdict"):
        lines.append(f"\n🎯 <b>Итоговая рекомендация:</b>\n{data['verdict']}")

    lines.append("\n💬 <i>Вы находитесь в режиме исследования. Можете задавать уточняющие вопросы или прислать новую тему!</i>")
    return "\n".join(lines)


def format_factcheck_card(data: dict) -> str:
    lines = [
        "🛡 <b>Результат фактчекинга и проверки новости:</b>\n",
        f"💬 <b>Тезис:</b> <i>«{data.get('claim')}»</i>\n",
        f"⚖️ <b>Вердикт:</b> <b>{data.get('verdict')}</b> (Точность: <b>{data.get('confidence')}%</b>)",
        f"📢 <b>Уровень кликбейта:</b> <i>{data.get('clickbait')}</i>\n",
        f"🔍 <b>Фактическая картина:</b>\n{data.get('real_facts')}\n"
    ]
    
    mans = data.get("manipulations", [])
    if mans:
        lines.append("⚠️ <b>Обнаруженные манипуляции:</b>")
        for m in mans:
            lines.append(f"  • {m}")

    lines.append("\n💬 <i>Режим фактчека активен. Присылайте любые утверждения или ссылки для проверки!</i>")
    return "\n".join(lines)


@router.message(Command("research"))
@router.message(F.text.in_(["🔬 Ресерч", "🔬 Deep Research & 🛡 Фактчек", "🔬 Deep Research", "🔬 Исследования", "Ресерч", "Deep Research"]))
async def cmd_research_menu(message: types.Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔬 Начать глубокое исследование", callback_data="mode_start_research")],
            [InlineKeyboardButton(text="🛡 Проверить новость на фейк", callback_data="mode_start_factcheck")]
        ]
    )
    await message.answer(
        "🔬 <b>Аналитический центр Deep Research & Fact-Checker:</b>\n\n"
        "Выберите режим работы:\n"
        "• <b>Deep Research</b> — автономный сбор данных, сравнение вариантов, плюсы/минусы и итоговый вердикт.\n"
        "• <b>Фактчекер</b> — проверка новостей и слухов на достоверность, манипуляции и кликбейт.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )


@router.callback_query(F.data == "mode_start_research")
async def cb_start_research(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.research_mode)
    text = (
        "🔬 <b>Режим «Deep Research» активирован!</b>\n\n"
        "Напишите любую тему для глубокого анализа (техника, автомобили, бизнес, научные вопросы):\n"
        "👉 <i>«Сравни лучшие зимние шины для СПб 2026: шипы vs липучка»</i>\n"
        "👉 <i>«Какой роутер с поддержкой Wi-Fi 7 и VLESS выбрать для дома?»</i>\n\n"
        "💡 <i>Все сообщения будут обрабатываться как запросы на исследование, пока вы не нажмете кнопку завершения ниже.</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Deep Research"))
    await callback.answer()


@router.callback_query(F.data == "mode_start_factcheck")
async def cb_start_factcheck(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.factcheck_mode)
    text = (
        "🛡 <b>Режим «Фактчекинг новостей» активирован!</b>\n\n"
        "Пришлите заголовок новости, цитату или слух:\n"
        "👉 <i>«В СПб вводят налог на кондиционеры с 1 сентября»</i>\n"
        "👉 <i>«Правда ли, что с 2026 года отменяют скидку 50% на штрафы ГИБДД?»</i>\n\n"
        "💡 <i>Бот проверит первоисточники и вынесет вердикт достоверности.</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Фактчек"))
    await callback.answer()


@router.message(ActiveModeStates.research_mode)
async def handle_research_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Deep Research» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await conduct_deep_research(user_id, text)
    reply = format_research_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Deep Research"))


@router.message(ActiveModeStates.factcheck_mode)
async def handle_factcheck_dialog(message: types.Message, state: FSMContext):
    text = message.text or ""
    if text in ["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit", "Отмена", "отмена"]:
        await state.clear()
        await message.answer("🏁 <b>Режим «Фактчекинг» завершен.</b> Вы вернулись в главное меню.", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    data = await verify_claim_or_news(user_id, text)
    reply = format_factcheck_card(data)
    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Фактчек"))
