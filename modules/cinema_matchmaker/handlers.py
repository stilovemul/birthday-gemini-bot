import io
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
    get_last_recommended_movies,
    get_active_search_context,
    mark_all_last_recommended_as_watched
)
from modules.voice_assistant.transcriber import transcribe_audio_gemini

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
            InlineKeyboardButton(text="👀 Всё это смотрел (Ещё)", callback_data="cm_watched_all"),
        ])
        buttons.append([
            InlineKeyboardButton(text="🔄 Ещё 5 вариантов", callback_data="cm_more"),
            InlineKeyboardButton(text="📚 Мой профиль вкуса", callback_data="cm_taste_profile")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="📚 Мой профиль вкуса", callback_data="cm_taste_profile")
        ])

    buttons.append([
        InlineKeyboardButton(text="🇷🇺 Сериалы РФ", callback_data="cm_filter_ru_series"),
        InlineKeyboardButton(text="🌍 Зарубежные", callback_data="cm_filter_foreign_series"),
        InlineKeyboardButton(text="🎬 Фильмы", callback_data="cm_filter_movies"),
    ])

    buttons.append([
        InlineKeyboardButton(text="🏁 Главное меню", callback_data="mode_exit_to_main")
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
                InlineKeyboardButton(text="🎬 Подобрать 5 вариантов под вкус", callback_data="cm_refresh_with_taste"),
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
        "🎬 <b>AI-Киносомелье & Мыслительный Рекомендатор:</b>\n\n"
        "Я подбираю <b>5 идеальных фильмов и сериалов</b> не по скучным алгоритмам, а по <b>атмосфере, режиссерскому почерку, драматургии и вашим любимым референсам</b>!\n\n"
        "🧠 <b>Мыслительный модуль и непрерывная память:</b>\n"
        "• <b>Расскажите, что смотрите сейчас или смотрели ранее</b> (например: <i>«Мы сейчас смотрим ЮЗЗЗ, очень нравится, еще смотрели Капельник, хотим подобный русский сериал»</i>).\n"
        "• <b>Если уже всё видели</b> — просто напишите <i>«всё смотрел, давай другое»</i> или нажмите кнопку <b>[ 👀 Всё это смотрел (Ещё) ]</b>. Бот мгновенно отправит эти картины в черный список и найдет новые без повторов!\n"
        "• <b>Ставьте оценки</b> кнопками <b>[ 👍 #1..#5 ]</b> под списком.\n\n"
        f"📊 <b>В вашей фильмотеке:</b> {len(watched)} картин (👍 Понравилось: {liked_count}, 👎 Не зашло: {disliked_count})\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Хочу русский криминальный сериал с драйвом и юмором в духе ЮЗЗЗ и Лады Голд»</i>\n"
        "• <i>«Посоветуй закрученный детективный триллер на вечер»</i>\n"
        "• <i>«Что посмотреть с девушкой под пиццу?»</i>\n\n"
        "💬 <i>Напишите запрос, отзыв или надиктуйте голосом:</i>"
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


@router.callback_query(F.data.in_(["cm_more", "cm_new_search"]))
async def cb_cinema_more(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("🔄 Подбираю 5 новых вариантов без повторов...")
    
    ctx = get_active_search_context(callback.from_user.id)
    last_q = ctx.get("last_query") or "дай еще 5 вариантов"
    result = await recommend_movies(callback.from_user.id, f"покажи еще 5 других вариантов (предыдущий запрос: {last_q})")
    await render_movie_recommendations(callback.message, result)


@router.callback_query(F.data == "cm_watched_all")
async def cb_cinema_watched_all(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("👀 Запомнил все 5 картин как просмотренные! Ищу новые...", show_alert=False)
    
    result = await recommend_movies(callback.from_user.id, "всё смотрел, давай другое что-нибудь")
    await render_movie_recommendations(callback.message, result)


@router.callback_query(F.data == "cm_filter_ru_series")
async def cb_filter_ru_series(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("🇷🇺 Ищу топовые российские сериалы...")
    
    result = await recommend_movies(callback.from_user.id, "хочу отличный русский сериал под мой вкус")
    await render_movie_recommendations(callback.message, result)


@router.callback_query(F.data == "cm_filter_foreign_series")
async def cb_filter_foreign_series(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("🌍 Ищу зарубежные сериалы...")
    
    result = await recommend_movies(callback.from_user.id, "посоветуй зарубежный сериал с высоким рейтингом")
    await render_movie_recommendations(callback.message, result)


@router.callback_query(F.data == "cm_filter_movies")
async def cb_filter_movies(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("🎬 Подбираю полнометражные фильмы...")
    
    result = await recommend_movies(callback.from_user.id, "посоветуй отличный полнометражный фильм на вечер")
    await render_movie_recommendations(callback.message, result)


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
                f"Картина <b>«{m_title}»</b> добавлена в список понравившихся (👍).\n"
                f"Профиль вкуса обновлен! Она исключена из будущих подборок.\n\n"
                f"💬 Подобрать 5 новых вариантов с учетом этой оценки?",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎬 Подобрать 5 вариантов под обновленный вкус", callback_data="cm_refresh_with_taste")],
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
    await callback.answer("Выберите номер картины, которая не понравилась")


@router.callback_query(F.data.startswith("cm_dislike_"))
async def cb_quick_dislike(callback: types.CallbackQuery, state: FSMContext):
    idx_str = callback.data.replace("cm_dislike_", "")
    try:
        idx = int(idx_str)
        res = await process_quick_rating(callback.from_user.id, idx, "disliked")
        if res.get("success"):
            m_title = html.escape(str(res.get("movie_title", f"Фильм #{idx}")))
            await callback.answer(f"👎 Запомнил: «{m_title}» не зашел", show_alert=False)
            await callback.message.reply(
                f"🧠 <b>Зафиксировано в памяти:</b>\n"
                f"Картина <b>«{m_title}»</b> отмечена как не понравившаяся (👎).\n"
                f"Бот скорректировал фильтры и больше не будет рекомендовать подобные ходы.\n\n"
                f"💬 Подобрать 5 новых вариантов с учетом исключений?",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎬 Подобрать 5 вариантов под обновленный вкус", callback_data="cm_refresh_with_taste")],
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
        lines.append(f"🎬 <b>Любимые режиссеры/шоураннеры:</b> {', '.join(fav_dirs)}")
    if fav_genres:
        lines.append(f"🎭 <b>Любимые стили/жанры:</b> {', '.join(fav_genres)}")
    if disliked:
        lines.append(f"🚫 <b>Избегать в рекомендациях:</b> {', '.join(disliked)}")

    lines.append(f"\n👍 <b>Понравилось ({len(liked_list)}):</b>")
    if liked_list:
        lines.extend(liked_list[:12])
    else:
        lines.append("<i>Пока нет оцененных картин с лайком</i>")

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
        "🗑 <b>Память кинопрофиля и просмотренных картин очищена.</b>\n"
        "Теперь вы можете начать формировать рекомендации с чистого листа!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cinema_keyboard(has_movies=False)
    )


@router.callback_query(F.data == "cm_refresh_with_taste")
async def cb_refresh_with_taste(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.cinema_matchmaker_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer("Подбираю 5 вариантов под обновленный вкус...")
    
    result = await recommend_movies(callback.from_user.id, "Посоветуй 5 идеальных вариантов под мой обновленный профиль вкуса")
    await render_movie_recommendations(callback.message, result)


async def render_movie_recommendations(message: types.Message, result: dict):
    thought = html.escape(str(result.get("thought_process", "")))
    mood = html.escape(str(result.get("mood_summary", "Подборка картин")))
    movies = result.get("movies", [])
    setup = html.escape(str(result.get("viewing_setup", "")))

    lines = []
    if thought:
        lines.append(f"🧠 <b>Мыслительный анализ вкуса:</b>\n<i>{thought}</i>\n")

    lines.append(f"🎬 <b>ТОП-5 ПЕРСОНАЛЬНЫХ РЕКОМЕНДАЦИЙ:</b>")
    lines.append(f"🎯 <b>Вайб и атмосфера:</b> <i>«{mood}»</i>\n━━━━━━━━━━━━━━━━━━━")

    for idx, m in enumerate(movies[:5], 1):
        ru_t = html.escape(str(m.get("title_ru", "Картина")))
        orig_t = html.escape(str(m.get("title_orig", "")))
        director = html.escape(str(m.get("director", "")))
        genres = html.escape(str(m.get("genres", "")))
        ratings = html.escape(str(m.get("ratings", "⭐️ 8.0")))
        why = html.escape(str(m.get("why_match", "")))
        plot = html.escape(str(m.get("plot_hook", "")))
        where = html.escape(str(m.get("where_to_watch", "Онлайн-кинотеатры")))

        lines.append(
            f"<b>{idx}. 🍿 {ru_t}</b> <i>({orig_t})</i>\n"
            f"   🎬 Режиссер/Создатели: <b>{director}</b> | {genres}\n"
            f"   ⭐️ <b>Рейтинг:</b> {ratings}\n"
            f"   🎯 <b>Почему вам понравится:</b> <i>{why}</i>\n"
            f"   📖 <b>Завязка:</b> {plot}\n"
            f"   📺 <b>Где смотреть:</b> <code>{where}</code>\n"
        )

    if setup:
        lines.append(f"🍻 <b>Идеальный сетап к просмотру:</b>\n<i>{setup}</i>\n")

    lines.append("<i>👇 Оцените кнопками ниже, нажмите «Всё это смотрел» для новой выдачи или напишите отзыв в чат:</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_cinema_keyboard(has_movies=True))


@router.message(ActiveModeStates.cinema_matchmaker_mode, F.voice | F.video_note | F.audio)
async def handle_cinema_voice(message: types.Message, state: FSMContext):
    """Voice input support for Cinema Matchmaker."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    file_id = None
    if message.voice:
        file_id = message.voice.file_id
    elif message.video_note:
        file_id = message.video_note.file_id
    elif message.audio:
        file_id = message.audio.file_id

    if not file_id:
        await message.answer("⚠️ Не удалось прочитать голосовое сообщение.")
        return

    try:
        file_info = await message.bot.get_file(file_id)
        file_bytes_io = io.BytesIO()
        await message.bot.download_file(file_info.file_path, file_bytes_io)
        file_bytes_io.seek(0)
        audio_bytes = file_bytes_io.read()
    except Exception as e:
        logger.warning(f"Error downloading cinema voice: {e}")
        await message.answer("⚠️ Не удалось загрузить аудиосообщение. Напишите текстом.")
        return

    transcribed = await transcribe_audio_gemini(audio_bytes)
    if not transcribed:
        await message.answer("🎙 Не удалось расслышать голосовое сообщение. Попробуйте повторить или написать текстом.")
        return

    await message.answer(f"🎙 <b>Вы сказали:</b> <i>«{html.escape(transcribed)}»</i>", parse_mode=ParseMode.HTML)

    result = await recommend_movies(message.from_user.id, transcribed)
    await render_movie_recommendations(message, result)


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
