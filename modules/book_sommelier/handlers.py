import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.book_sommelier.sommelier import get_book_recommendation_or_summary

logger = logging.getLogger("BookSommelierHandlers")
router = Router(name="book_sommelier")


def get_book_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡️ Саммари: Атомные привычки", callback_data="bk_sum_atomic"),
                InlineKeyboardButton(text="🧠 Саммари: Думай медленно... (Канеман)", callback_data="bk_sum_kahneman")
            ],
            [
                InlineKeyboardButton(text="💰 Саммари: Психология денег", callback_data="bk_sum_money"),
                InlineKeyboardButton(text="🎯 Саммари: Эссенциализм", callback_data="bk_sum_essential")
            ],
            [
                InlineKeyboardButton(text="📚 Топ книг по переговорам и бизнесу", callback_data="bk_list_business"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("books"))
@router.message(Command("book"))
@router.message(F.text.in_(["📚 Книги", "Книги", "Книжный сомелье", "Саммари книг"]))
async def cmd_book_sommelier(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.book_sommelier_mode)
    text = (
        "📚 <b>Книжный Сомелье & 15-минутные выжимки бестселлеров:</b>\n\n"
        "Я делаю **сжатые конспекты ключевых мыслей** без воды и подбираю книги под любые задачи!\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Сделай выжимку книги Принципы Рэя Далио»</i>\n"
        "• <i>«Главные мысли книги Черный лебедь Нассима Талеба»</i>\n"
        "• <i>«Посоветуй захватывающий детектив в духе Скандинавии»</i>\n"
        "• <i>«Топ-3 книги по инвестициям и мышлению богатых»</i>\n\n"
        "💬 <i>Напишите название книги или тему:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Книги"))
    await message.answer("👇 <b>Быстрые выжимки мировых бестселлеров:</b>", reply_markup=get_book_keyboard())


@router.callback_query(F.data.startswith("bk_"))
async def cb_book_preset(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.book_sommelier_mode)
    data = callback.data.replace("bk_", "")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    presets = {
        "sum_atomic": "Выжимка книги Атомные привычки Джеймса Клира",
        "sum_kahneman": "Выжимка книги Думай медленно... решай быстро Даниэля Канемана",
        "sum_money": "Выжимка книги Психология денег Моргана Хаузела",
        "sum_essential": "Выжимка книги Эссенциализм Грега МакКеона",
        "list_business": "Топ-4 лучших практических книг по переговорам, лидерству и бизнесу"
    }
    q = presets.get(data, "Лучшие книги по саморазвитию")
    await callback.answer("Готовлю литературный конспект...")
    res = await get_book_recommendation_or_summary(callback.from_user.id, q)
    await render_book_results(callback.message, res)


@router.message(ActiveModeStates.book_sommelier_mode, F.text)
async def handle_book_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Книжный сомелье» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await get_book_recommendation_or_summary(message.from_user.id, raw_text)
    await render_book_results(message, res)


async def render_book_results(message: types.Message, res: dict):
    title = html.escape(str(res.get("title", "Книга")))
    author = html.escape(str(res.get("author_year", "")))
    thesis = html.escape(str(res.get("core_thesis", "")))
    takeaways = res.get("key_takeaways", [])
    step = html.escape(str(res.get("actionable_step", "")))
    rec_books = res.get("recommended_books", [])

    lines = [
        f"📚 <b>{title.upper()}</b>" + (f" <i>({author})</i>\n" if author else "\n"),
        f"🎯 <b>Главная суть:</b>\n<i>«{thesis}»</i>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    if takeaways:
        lines.append("💡 <b>КЛЮЧЕВЫЕ ИНСАЙТЫ И ПРАВИЛА:</b>")
        for t in takeaways:
            lines.append(f"• {html.escape(str(t))}")
        lines.append("")

    if step:
        lines.append(f"⚡️ <b>Практическое действие на сегодня:</b>\n👉 <i>{step}</i>\n")

    if rec_books:
        lines.append("📖 <b>РЕКОМЕНДОВАННЫЕ КНИГИ:</b>")
        for b in rec_books:
            b_title = html.escape(str(b.get("title", "")))
            b_auth = html.escape(str(b.get("author", "")))
            b_why = html.escape(str(b.get("why", "")))
            lines.append(f"• <b>{b_title}</b> ({b_auth}) — <i>{b_why}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_book_keyboard())
