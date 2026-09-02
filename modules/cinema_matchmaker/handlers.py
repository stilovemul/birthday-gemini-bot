import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.cinema_matchmaker.recommender import recommend_movies, process_quick_rating
from modules.cinema_matchmaker.storage import (
    get_user_cinema_memory,
    clear_user_cinema_memory,
    get_last_recommended_movies
)

logger = logging.getLogger("CinemaMatchmakerHandlers")
router = Router(name="cinema_matchmaker")


def get_cinema_keyboard(has_movies: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if has_movies:
        buttons.append([
            InlineKeyboardButton(text="👍 #1", callback_data="cm_like_1"),
            InlineKeyboardButton(text="👍 #2", callback_data="cm_like_2"),
            InlineKeyboardButton(text="👍 #3", callback_data="cm_like_3"),
            InlineKeyboardButton(text="👍 #4", callback_data="cm_like_4"),
            InlineKeyboardButton(text="👍 #5", callback_data="cm_like_5"),
        ])
        buttons.append([
            InlineKeyboardButton(text="👎 Не зашло (#1-#5)", callback_data="cm_dislike_menu"),
            InlineKeyboardButton(text="📚 Мой профиль вкуса", callback_data="cm_taste_profile")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="📚 Мой профиль вкуса", callback_data="cm_taste_profile")
        ])

    buttons.append([
        InlineKeyboardButton(text="🎲 Еще 5 фильмов", callback_data="cm_new_search"),
        InlineKeyboardButton(text="🚪 Выйти", callback_data="mode_exit_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_dislike_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👎 #1", callback_data="cm_dislike_1"),
                InlineKeyboardButton(text="👎 #2", callback_data="cm_dislike_2"),
                InlineKeyboardButton(text="👎 #3", callback_data="cm_dislike_3"),
                InlineKeyboardButton(text="👎 #4", callback_data="cm_dislike_4"),
                InlineKeyboardButton(text="👎 #5", callback_data="cm_dislike_5"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад к подборке", callback_data="cm_back_to_movies")
            ]
        ]
    )


def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Подобрать 5 фильмов под вкус", callback_data="cm_new_search"),
            ],
            [
                InlineKeyboardButton(text="🗑 Очистить память вкуса", callback_data="cm_clear_profile_confirm"),
                InlineKeyboardButton(text="🔙 Назад к подборке", callback_data="cm_back_to_movies")
            ]
        ]
    )


@router.message(Command("cinema"))
@router.message(Command("movie"))
@router.message(F.text.in_(["🎬 Кино", "🎬 Кино & Сериалы", "🎬 Киноподборщик", "Кино", "Фильмы", "Сериалы"]))
async def cmd_cinema_matchmaker(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    
    user_mem = get_user_cinema_memory(message.from_user.id)
    watched = user_mem.get("watched_movies", [])
    liked_count = len([w for w in watched if w.get("status") == "liked"])
    disliked_count = len([w for w in watched if w.get("status") == "disliked"])

    text = (
        "🎬 <b>AI-Киноподборщик & Мыслительный Киносомелье:</b>\n\n"
        "Я подбираю <b>5 идеальных фильмов и сериалов</b> не по скучным жанрам, а по <b>атмосфере, режиссерскому почерку и вашим любимым референсам</b>!\n\n"
        "🧠 <b>Мыслительный модуль и самообучение:</b>\n"
        "• Назовите фильм, который вы смотрели и как он вам (например: <i>«Смотрел 1-й фильм / Залечь на дно в Брюгге, очень зашел!»</i>).\n"
        "• Либо ставьте быструю оценку кнопками <b>[ 👍 #1..#5 ]</b> под подборкой.\n"
        "• Бот мгновенно запоминает ваши предпочтения в долговременную память и исключает просмотренные картины из будущих рекомендаций!\n\n"
        f"📊 <b>В вашей фильмотеке:</b> {len(watched)} фильмов (👍 Понравилось: {liked_count}, 👎 Не зашло: {disliked_count})\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Смотрел 'Однажды в Ирландии', хочу похожее с черным юмором»</i>\n"
        "• <i>«Люблю ранние фильмы Гая Ричи и Тарантино»</i>\n"
        "• <i>«Посоветуй напряженный детектив в замкнутом пространстве»</i>\n"
        "• <i>«Что посмотреть на вечер под пиццу?»</i>\n\n"
        "💬 <i>Напишите запрос или отзыв на любой фильм:</i>"
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
        "💬 <b>Напишите новый фильм-референс, режиссера, настроение или пожелание к просмотру:</b>\n"
        "<i>(Либо напишите, какие фильмы смотрели и как они вам — бот обновит профиль вкуса!)</i>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cm_like_"))
async def cb_quick_like(callback: types.CallbackQuery, state: FSMContext):
    idx_str = callback.data.replace("cm_like_", "")
    try:
        idx = int(idx_str)
        res = await process_quick_rating(callback.from_user.id, idx, "liked")
        if res.get("success"):
            m_title = html.escape(str(res.get("movie_title", f"Фильм #{idx}")))
            await callback.answer(f"👍 Запомнил: «{m_title}» вам понравился!", show_alert=False)
            await callback.message.reply(
                f"🧠 <b>Зафиксировано в памяти:</b>\n"
                f"Фильм <b>«{m_title}»</b> добавлен в список понравившихся (👍).\n"
                f"Профиль вкуса обновлен! Фильм исключен из будущих подборок.\n\n"
                f"💬 Хотите подобрать 5 новых фильмов с учетом этой оценки?",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎬 Подобрать 5 фильмов под обновленный вкус", callback_data="cm_refresh_with_taste")],
                    [InlineKeyboardButton(text="📚 Мой профиль вкуса", callback_data="cm_taste_profile")]
                ])
            )
        else:
            await callback.answer(res.get("message", "Ошибка"), show_alert=True)
    except Exception as e:
        logger.error(f"Error in quick like: {e}")
        await callback.answer("Ошибка при сохранении оценки")


@router.callback_query(F.data == "cm_dislike_menu")
async def cb_dislike_menu(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=get_dislike_keyboard())
    await callback.answer("Выберите номер фильма, который не понравился")


@router.callback_query(F.data.startswith("cm_dislike_"))
async def cb_quick_dislike(callback: types.CallbackQuery, state: FSMContext):
    idx_str = callback.data.replace("cm_dislike_", "")
    try:
        idx = int(idx_str)
        res = await process_quick_rating(callback.from_user.id, idx, "disliked")
        if res.get("success"):
            m_title = html.escape(str(res.get("movie_title", f"Фильм #{idx}")))
            await callback.answer(f"👎 Запомнил: «{m_title}» не понравился", show_alert=False)
            await callback.message.reply(
                f"🧠 <b>Зафиксировано в памяти:</b>\n"
                f"Фильм <b>«{m_title}»</b> отмечен как не понравившийся (👎).\n"
                f"Бот скорректировал фильтры и больше не будет рекомендовать подобные приемы.\n\n"
                f"💬 Подобрать 5 новых фильмов с учетом исключений?",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎬 Подобрать 5 фильмов под обновленный вкус", callback_data="cm_refresh_with_taste")],
                    [InlineKeyboardButton(text="📚 Мой профиль вкуса", callback_data="cm_taste_profile")]
                ])
            )
        else:
            await callback.answer(res.get("message", "Ошибка"), show_alert=True)
    except Exception as e:
        logger.error(f"Error in quick dislike: {e}")
        await callback.answer("Ошибка при сохранении оценки")


@router.callback_query(F.data == "cm_back_to_movies")
async def cb_back_to_movies(callback: types.CallbackQuery):
    last_movies = get_last_recommended_movies(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=get_cinema_keyboard(has_movies=bool(last_movies)))
    await callback.answer()


@router.callback_query(F.data == "cm_taste_profile")
async def cb_show_taste_profile(callback: types.CallbackQuery):
    user_mem = get_user_cinema_memory(callback.from_user.id)
    watched = user_mem.get("watched_movies", [])
    taste_summary = html.escape(str(user_mem.get("taste_summary", "Вкусовой профиль формируется...")))
    fav_genres = [html.escape(str(g)) for g in user_mem.get("favorite_genres", [])]
    fav_dirs = [html.escape(str(d)) for d in user_mem.get("favorite_directors", [])]
    disliked = [html.escape(str(t)) for t in user_mem.get("disliked_tropes", [])]

    liked_list = [f"• <b>{html.escape(w['title'])}</b>" + (f" <i>(реж. {html.escape(w['director'])})</i>" if w.get('director') else "") for w in watched if w.get("status") == "liked"]
    disliked_list = [f"• <b>{html.escape(w['title'])}</b>" + (f" <i>(реж. {html.escape(w['director'])})</i>" if w.get('director') else "") for w in watched if w.get("status") == "disliked"]

    lines = [
        "📚 <b>ВАШ ПЕРСОНАЛЬНЫЙ ПРОФИЛЬ КИНОМАНА:</b>\n",
        f"🧠 <b>Анализ вкуса от ИИ:</b>\n<i>«{taste_summary}»</i>\n"
    ]

    if fav_dirs:
        lines.append(f"🎬 <b>Любимые режиссеры:</b> {', '.join(fav_dirs)}")
    if fav_genres:
        lines.append(f"🎭 <b>Любимые стили/жанры:</b> {', '.join(fav_genres)}")
    if disliked:
        lines.append(f"🚫 <b>Избегать в рекомендациях:</b> {', '.join(disliked)}")

    lines.append(f"\n👍 <b>Понравилось ({len(liked_list)}):</b>")
    if liked_list:
        lines.extend(liked_list[:12])
    else:
        lines.append("<i>Пока нет оцененных фильмов с лайком</i>")

    if disliked_list:
        lines.append(f"\n👎 <b>Не зашло ({len(disliked_list)}):</b>")
        lines.extend(disliked_list[:8])

    await callback.message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cm_clear_profile_confirm")
async def cb_clear_profile(callback: types.CallbackQuery):
    clear_user_cinema_memory(callback.from_user.id)
    await callback.answer("Память кинопрофиля успешно очищена!", show_alert=True)
    await callback.message.answer(
        "🗑 <b>Память кинопрофиля и просмотренных фильмов очищена.</b>\n"
        "Теперь вы можете начать формировать рекомендации с чистого листа!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cinema_keyboard(has_movies=False)
    )


@router.callback_query(F.data == "cm_refresh_with_taste")
async def cb_refresh_with_taste(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("Подбираю 5 фильмов с учетом обновленного вкуса...")
    
    result = await recommend_movies(callback.from_user.id, "Посоветуй 5 идеальных фильмов под мой обновленный профиль вкуса")
    await render_movie_recommendations(callback.message, result)


async def render_movie_recommendations(message: types.Message, result: dict):
    thought = html.escape(str(result.get("thought_process", "")))
    mood = html.escape(str(result.get("mood_summary", "Подборка фильмов")))
    movies = result.get("movies", [])
    setup = html.escape(str(result.get("viewing_setup", "")))

    lines = []
    if thought:
        lines.append(f"🧠 <b>Мыслительный анализ вкуса:</b>\n<i>{thought}</i>\n")

    lines.append(f"🎬 <b>ТОП-5 ПЕРСОНАЛЬНЫХ РЕКОМЕНДАЦИЙ:</b>")
    lines.append(f"🎯 <b>Вайб и атмосфера:</b> <i>«{mood}»</i>\n━━━━━━━━━━━━━━━━━━━")

    for idx, m in enumerate(movies[:5], 1):
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
        lines.append(f"🍻 <b>Идеальный сетап к просмотру:</b>\n<i>{setup}</i>\n")

    lines.append("<i>👇 Оцените фильмы кнопками ниже или напишите отзывом в чат, чтобы еще точнее обучить бот вашему вкусу:</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_cinema_keyboard(has_movies=True))


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
    await render_movie_recommendations(message, result)
