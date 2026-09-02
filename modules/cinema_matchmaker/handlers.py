import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.cinema_matchmaker.recommender import recommend_movies

logger = logging.getLogger("CinemaMatchmakerHandlers")
router = Router(name="cinema_matchmaker")


def get_cinema_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Подобрать ещё кино", callback_data="cm_new_search"),
                InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("cinema"))
@router.message(Command("movie"))
@router.message(F.text.in_(["🎬 Кино", "🎬 Кино & Сериалы", "🎬 Киноподборщик", "Кино", "Фильмы", "Сериалы"]))
async def cmd_cinema_matchmaker(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    text = (
        "🎬 <b>AI-Киноподборщик & Киносомелье:</b>\n\n"
        "Я подбираю фильмы и сериалы не по банальным жанрам, а по <b>атмосфере, режиссерскому почерку и вашим любимым референсам</b>!\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Смотрел 'Однажды в Ирландии', хочу похожее с черным юмором»</i>\n"
        "• <i>«Люблю ранние фильмы Гая Ричи и Тарантино»</i>\n"
        "• <i>«Посоветуй напряженный детектив в замкнутом пространстве»</i>\n"
        "• <i>«Уютный сериал на выходные с осенней атмосферой»</i>\n\n"
        "💬 <i>Напишите, что вам понравилось или какое кино хочется посмотреть:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Киносомелье"))


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_cinema(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏁 <b>Режим «Киносомелье» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )
    await callback.answer("Вы вышли в главное меню")


@router.callback_query(F.data == "cm_new_search")
async def cb_cinema_new(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.message.answer(
        "💬 <b>Напишите новый фильм-референс, режиссера или пожелание к просмотру:</b>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(ActiveModeStates.cinema_matchmaker_mode, F.text)
async def handle_cinema_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Киносомелье» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    result = await recommend_movies(message.from_user.id, raw_text)

    mood = html.escape(str(result.get("mood_summary", "Подборка фильмов")))
    movies = result.get("movies", [])
    setup = html.escape(str(result.get("viewing_setup", "")))

    lines = [
        f"🎬 <b>ПЕРСОНАЛЬНАЯ КИНОПОДБОРКА:</b>\n",
        f"🎯 <b>Вайб и настроение:</b> <i>«{mood}»</i>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, m in enumerate(movies, 1):
        ru_t = html.escape(str(m.get("title_ru", "Фильм")))
        orig_t = html.escape(str(m.get("title_orig", "")))
        director = html.escape(str(m.get("director", "")))
        genres = html.escape(str(m.get("genres", "")))
        ratings = html.escape(str(m.get("ratings", "⭐️ 8.0")))
        why = html.escape(str(m.get("why_match", "")))
        plot = html.escape(str(m.get("plot_hook", "")))
        where = html.escape(str(m.get("where_to_watch", "Онлайн-кинотеатры")))

        lines.append(
            f"<b>{idx}. 🍿 {ru_t}</b> <i>({orig_t})</i>\n"
            f"   🎬 Режиссер: <b>{director}</b> | {genres}\n"
            f"   ⭐️ <b>Рейтинг:</b> {ratings}\n"
            f"   🎯 <b>Почему вам понравится:</b> <i>{why}</i>\n"
            f"   📖 <b>Завязка:</b> {plot}\n"
            f"   📺 <b>Где смотреть:</b> <code>{where}</code>\n"
        )

    if setup:
        lines.append(f"🍻 <b>Идеальный сетап к просмотру:</b>\n<i>{setup}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_cinema_keyboard())
