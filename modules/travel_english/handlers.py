"""
Обработчики модуля «🗣 Живой English (Travel & Street Smart)»:
- Точка входа, FSM-состояние, голосовой и текстовый ролевой диалог
- Интерактивные проверочные тесты / квизы с начислением XP
- Мгновенный перевод фраз на 3 стиля живого языка
- Золотые шпаргалки для путешествий
"""

import io
import random
import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.voice_assistant.transcriber import transcribe_audio_gemini
from modules.travel_english.formatter import send_clean_html, clean_telegram_html
from modules.travel_english.storage import (
    get_user_profile,
    add_user_xp,
    increment_dialogs_count,
    save_phrase
)
from modules.travel_english.scenarios_catalog import SCENARIOS, get_scenario_info
from modules.travel_english.quizzes_catalog import (
    QUIZ_CATEGORIES,
    QUESTIONS_DATA,
    get_quiz_by_id,
    get_category_questions
)
from modules.travel_english.cheat_sheets import CHEAT_SHEETS
from modules.travel_english.keyboards import (
    get_travel_english_main_keyboard,
    get_scenarios_keyboard,
    get_dialog_actions_keyboard,
    get_quiz_categories_keyboard,
    get_quiz_options_keyboard,
    get_quiz_result_keyboard,
    get_cheat_sheets_keyboard
)
from modules.travel_english.simulator import simulate_dialog_turn, instant_translate_phrase

logger = logging.getLogger("TravelEnglishHandlers")
router = Router(name="travel_english")


# -------------------------------------------------------------
# 1. Точка входа в модуль «Живой English»
# -------------------------------------------------------------
@router.message(Command("english"))
@router.message(Command("travel_english"))
@router.message(F.text.func(lambda t: bool(t and any(k in t.lower() for k in [
    "живой english", "english", "разговорный английский", "английский для путешествий",
    "учить английский", "английский язык"
]))))
async def cmd_travel_english(message: types.Message, state: FSMContext):
    """Открывает главное интерактивное меню живого разговорного английского."""
    await state.set_state(ActiveModeStates.travel_english_mode)
    await state.update_data(
        current_scenario="",
        scenario_history="",
        turns=0,
        current_quiz_id="",
        awaiting_instant_translate=False
    )

    profile = get_user_profile(message.from_user.id)

    welcome_text = (
        "🗣 <b>Живой English: Разговорный английский без зубрежки</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Забудь занудные школьные правила, Past Perfect и таблицы времен! "
        "Здесь только <b>реальный язык для путешествий и общения с иностранцами</b>:\n\n"
        "• 🎭 <b>Ролевой тренажер:</b> реальные диалоги (кофейня, отель, аэропорт, бар, торг на рынке)\n"
        "• 🎙 <b>Голосовая тренировка:</b> говорите в чат голосом или кружочком — ИИ оценит произношение и естественность\n"
        "• 📝 <b>Проверочные квизы:</b> быстрые тесты на уличный сленг и реакции нейтивов (+XP к уровню)\n"
        "• ⚡️ <b>Перевод на лету:</b> как сказать любую мысль на уличном сленге с русской транскрипцией\n"
        "• 📋 <b>Золотые шпаргалки:</b> 50+ готовых фраз-выручалочек для поездок\n\n"
        f"🏆 <b>Твой статус:</b> {profile['level']} (⭐ {profile['xp']} XP)\n\n"
        "👇 <b>С чего начнем тренировку? Выбери режим:</b>"
    )

    await message.answer("Вход в режим «🗣 Живой English»...", reply_markup=get_mode_keyboard("Живой English"))
    await send_clean_html(message, welcome_text, reply_markup=get_travel_english_main_keyboard())


# -------------------------------------------------------------
# 2. Навигация по главным разделам модуля
# -------------------------------------------------------------
@router.callback_query(F.data == "eng_main_menu")
async def cb_eng_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню модуля."""
    await state.set_state(ActiveModeStates.travel_english_mode)
    await state.update_data(awaiting_instant_translate=False)
    profile = get_user_profile(callback.from_user.id)

    text = (
        "🗣 <b>Главное меню «Живой English»</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 <b>Уровень:</b> {profile['level']}\n"
        f"⭐️ <b>Опыт:</b> {profile['xp']} XP | 🎯 <b>Правильных ответов:</b> {profile['correct_answers']}/{profile['total_questions']}\n\n"
        "Выбери нужный режим для прокачки разговорного навыка:"
    )
    await callback.answer()
    await send_clean_html(callback, text, reply_markup=get_travel_english_main_keyboard())


@router.callback_query(F.data == "eng_menu_scenarios")
async def cb_eng_menu_scenarios(callback: types.CallbackQuery, state: FSMContext):
    """Открывает список бытовых сценариев для ролевого диалога."""
    await callback.answer()
    text = (
        "🎭 <b>Ролевой тренажер: Реальные ситуации за границей</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Ты окажешься в реальной бытовой ситуации один на один с иностранцем. "
        "Отвечать можно <b>текстом или голосовыми сообщениями 🎙</b>!\n\n"
        "После каждой фразы тренер даст <b>Native Score (1-10)</b>, русскую транскрипцию и подскажет, "
        "как сказать это еще естественнее на живом сленге.\n\n"
        "👇 <b>Выбери локацию для практики:</b>"
    )
    await send_clean_html(callback, text, reply_markup=get_scenarios_keyboard())


# -------------------------------------------------------------
# 3. Запуск конкретного сценария диалога
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("eng_sc_"))
async def cb_start_scenario(callback: types.CallbackQuery, state: FSMContext):
    """Инициализирует выбранный ролевой сценарий."""
    sc_key = callback.data.replace("eng_sc_", "").strip()
    sc_info = get_scenario_info(sc_key)

    await state.set_state(ActiveModeStates.travel_english_mode)
    await state.update_data(
        current_scenario=sc_key,
        scenario_history="",
        turns=0,
        awaiting_instant_translate=False
    )

    await callback.answer()

    opening_msg = (
        f"{sc_info['icon']} <b>Ситуация: {sc_info['title']}</b>\n"
        f"👤 <b>Персонаж:</b> {sc_info['character']}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 <i>{sc_info['situation']}</i>\n\n"
        f"💬 <b>Реплика собеседника:</b>\n"
        f"«<b>{sc_info['opening_line']}</b>»\n\n"
        f"{sc_info['starter_tip']}\n\n"
        "✍️ Напиши свой ответ текстом или <b>надиктуй голосом 🎙</b> (как в реальной жизни!):"
    )

    await send_clean_html(callback, opening_msg, reply_markup=get_dialog_actions_keyboard())


@router.callback_query(F.data == "eng_action_restart")
async def cb_restart_scenario(callback: types.CallbackQuery, state: FSMContext):
    """Перезапускает текущий ролевой сценарий с чистого листа."""
    data = await state.get_data()
    sc_key = data.get("current_scenario", "bar_dating")
    sc_info = get_scenario_info(sc_key)

    await state.update_data(
        scenario_history="",
        turns=0,
        awaiting_instant_translate=False
    )
    await callback.answer("Начинаем диалог заново!")

    opening_msg = (
        f"{sc_info['icon']} <b>Ситуация: {sc_info['title']}</b>\n"
        f"👤 <b>Персонаж:</b> {sc_info['character']}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 <i>{sc_info['situation']}</i>\n\n"
        f"💬 <b>Реплика собеседника:</b>\n"
        f"«<b>{sc_info['opening_line']}</b>»\n\n"
        f"{sc_info['starter_tip']}\n\n"
        "✍️ Напиши свой ответ текстом или <b>надиктуй голосом 🎙</b>:"
    )
    await send_clean_html(callback, opening_msg, reply_markup=get_dialog_actions_keyboard())


@router.callback_query(F.data == "eng_action_suggest")
async def cb_suggest_reply(callback: types.CallbackQuery, state: FSMContext):
    """Выдает быстрые подсказки для ответа в текущем сценарии с переводом и транскрипцией."""
    data = await state.get_data()
    sc_key = data.get("current_scenario", "bar_dating")
    sc_info = get_scenario_info(sc_key)
    last_sugg = data.get("last_suggestions")

    tip_text = (
        "💡 <b>Шпаргалка: Что можно ответить прямо сейчас:</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if last_sugg:
        for idx, s in enumerate(last_sugg, 1):
            if isinstance(s, dict):
                tip_text += (
                    f"{idx}. <b>«{s.get('en')}»</b>\n"
                    f"   🗣 <i>{s.get('transcription', '')}</i>\n"
                    f"   — <i>{s.get('ru', '')}</i>\n\n"
                )
            else:
                tip_text += f"{idx}. <b>«{s}»</b>\n\n"
    else:
        replies = sc_info.get("suggested_replies", [
            "Hello! Yes, the seat is free.",
            "I am drinking juice. What about you?",
            "Nice to meet you! My name is Oleg."
        ])
        for idx, r in enumerate(replies, 1):
            tip_text += f"{idx}. <b>«{r}»</b>\n"

    tip_text += (
        "💬 Выбери любой вариант или скажи своими словами текстом / <b>голосом 🎙</b>!"
    )
    await callback.answer()
    await send_clean_html(callback, tip_text, reply_markup=get_dialog_actions_keyboard())


# -------------------------------------------------------------
# 4. Проверочные работы / Квизы
# -------------------------------------------------------------
@router.callback_query(F.data == "eng_menu_quizzes")
async def cb_eng_menu_quizzes(callback: types.CallbackQuery, state: FSMContext):
    """Меню категорий проверочных квизов."""
    await callback.answer()
    text = (
        "📝 <b>Проверочные работы: Street Smart Quizzes</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Проверь свое чутье на живой разговорный английский! "
        "Здесь нет вопросов по формулам времен — только реальные ситуации:\n\n"
        "• Как понять сленг бармена или официанта\n"
        "• Как не опозориться при заказе кофе или еды\n"
        "• Что на самом деле значат фразы «Don't sweat it» и «My bad»\n"
        "• Как сбивать цену и просить счет без неловкости\n\n"
        "За каждый правильный ответ начисляется <b>+10 XP</b> к твоему уровню!\n\n"
        "👇 <b>Выбери категорию теста:</b>"
    )
    await send_clean_html(callback, text, reply_markup=get_quiz_categories_keyboard())


@router.callback_query(F.data.startswith("eng_start_quiz_") | F.data.startswith("eng_next_quiz_"))
async def cb_run_quiz_question(callback: types.CallbackQuery, state: FSMContext):
    """Запускает вопрос из выбранной категории квиза."""
    raw = callback.data
    category = raw.replace("eng_start_quiz_", "").replace("eng_next_quiz_", "").strip()
    if not category:
        category = "blitz"

    questions = get_category_questions(category)
    if not questions:
        questions = QUESTIONS_DATA

    q = random.choice(questions)
    await state.update_data(current_quiz_id=q["id"], current_quiz_category=category)
    await callback.answer()

    text = (
        f"🎯 <b>Вопрос на проверку уличного английского:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 <i>{q['situation']}</i>\n\n"
        f"❓ <b>{q['question']}</b>\n\n"
        f"🅰️ {q['options'][0]}\n"
        f"🅱️ {q['options'][1]}\n"
        f"🅲 {q['options'][2]}\n"
        f"🅳 {q['options'][3]}\n\n"
        "👇 <b>Нажми на правильный вариант:</b>"
    )

    await send_clean_html(callback, text, reply_markup=get_quiz_options_keyboard(q["id"], q["options"]))


@router.callback_query(F.data.startswith("eng_ans_"))
async def cb_check_quiz_answer(callback: types.CallbackQuery, state: FSMContext):
    """Проверяет выбранный пользователем ответ на квиз."""
    parts = callback.data.split("_")
    # Формат: eng_ans_<qid>_<idx>
    if len(parts) < 4:
        await callback.answer("Ошибка формата", show_alert=True)
        return

    qid = parts[2]
    selected_idx = int(parts[3])

    q = get_quiz_by_id(qid)
    is_correct = (selected_idx == q["correct_idx"])
    user_id = callback.from_user.id

    xp_gained = 10 if is_correct else 2
    profile = add_user_xp(user_id, xp_gained, is_correct)

    if is_correct:
        header = f"✅ <b>В ТОЧКУ! (+{xp_gained} XP) 🎯</b>\n"
    else:
        header = f"❌ <b>ПОЧТИ, НО НЕ СОВСЕМ! (+{xp_gained} XP за попытку)</b>\n"

    res_text = (
        f"{header}"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 <b>Правильный ответ:</b> <i>{q['options'][q['correct_idx']]}</i>\n\n"
        f"{q['native_tip']}\n\n"
        f"🏆 <b>Твой опыт:</b> {profile['xp']} XP | Уровень: <b>{profile['level']}</b>"
    )

    await callback.answer("Ответ принят!")
    await send_clean_html(callback, res_text, reply_markup=get_quiz_result_keyboard(q["category"]))


# -------------------------------------------------------------
# 5. Золотые шпаргалки
# -------------------------------------------------------------
@router.callback_query(F.data == "eng_menu_cheats")
async def cb_eng_menu_cheats(callback: types.CallbackQuery, state: FSMContext):
    """Меню золотых шпаргалок."""
    await callback.answer()
    text = (
        "📋 <b>Золотые шпаргалки для поездок за границу</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Готовые фразы-выручалочки с переводом и <b>русской транскрипцией</b>. "
        "Сохраняй и используй прямо в путешествии:\n\n"
        "• ☕️ Кафе, Бар & Ресторан\n"
        "• ✈️ Аэропорт, Самолет & Граница\n"
        "• 🏨 Отель, Заезд & Быт\n"
        "• 🚕 Такси, Улица & Торг на рынке\n"
        "• 🕶 ТОП-10 фраз нейтивов, которые делают тебя своим\n\n"
        "👇 <b>Выбери нужную шпаргалку:</b>"
    )
    await send_clean_html(callback, text, reply_markup=get_cheat_sheets_keyboard())


@router.callback_query(F.data.startswith("eng_cs_"))
async def cb_show_cheat_sheet(callback: types.CallbackQuery, state: FSMContext):
    """Показывает выбранную шпаргалку."""
    cs_key = callback.data.replace("eng_cs_", "").strip()
    sheet = CHEAT_SHEETS.get(cs_key, CHEAT_SHEETS["food_drink"])

    await callback.answer()
    await send_clean_html(callback, sheet["content"], reply_markup=get_cheat_sheets_keyboard())


# -------------------------------------------------------------
# 6. Профиль пользователя и XP
# -------------------------------------------------------------
@router.callback_query(F.data == "eng_menu_profile")
async def cb_eng_menu_profile(callback: types.CallbackQuery, state: FSMContext):
    """Показывает статистику и достижения пользователя."""
    profile = get_user_profile(callback.from_user.id)
    await callback.answer()

    total_q = profile.get("total_questions", 0)
    correct_q = profile.get("correct_answers", 0)
    acc = round((correct_q / total_q * 100)) if total_q > 0 else 0

    text = (
        "📊 <b>Твой прогресс в «Живой English»</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎖 <b>Текущий ранг:</b> {profile['level']}\n"
        f"⭐️ <b>Опыт (XP):</b> {profile['xp']} XP\n"
        f"🎯 <b>Пройдено вопросов:</b> {total_q}\n"
        f"✅ <b>Правильных ответов:</b> {correct_q} ({acc}% точность)\n"
        f"💬 <b>Раундов ролевых диалогов:</b> {profile.get('dialogs_count', 0)}\n\n"
        "<i>💡 Совет тренера: Проходи хотя бы 3 квиза в день или 1 ролевой диалог голосом, "
        "чтобы развить языковую интуицию нейтива!</i>"
    )
    await send_clean_html(callback, text, reply_markup=get_travel_english_main_keyboard())


# -------------------------------------------------------------
# 7. Мгновенный перевод фразы на сленг
# -------------------------------------------------------------
@router.callback_query(F.data == "eng_menu_instant")
async def cb_eng_menu_instant(callback: types.CallbackQuery, state: FSMContext):
    """Режим мгновенного перевода фразы на 3 стиля живого языка."""
    await state.update_data(awaiting_instant_translate=True)
    await callback.answer()

    text = (
        "⚡️ <b>Как сказать это по-английски? (Перевод на сленг)</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Напиши любую русскую мысль или фразу (или <b>надиктуй голосом 🎙</b>) — например:\n\n"
        "• <i>«Как сказать бармену повторить то же самое?»</i>\n"
        "• <i>«Сделай скидку, у меня только наличка»</i>\n"
        "• <i>«Где здесь лучший кофе без сахара?»</i>\n"
        "• <i>«Высади меня на этом углу»</i>\n\n"
        "💬 <b>Отправь сообщение в чат прямо сейчас:</b>"
    )
    await send_clean_html(callback, text)


# -------------------------------------------------------------
# 8. Обработка голосовых сообщений (F.voice | F.video_note | F.audio)
# -------------------------------------------------------------
@router.message(ActiveModeStates.travel_english_mode, F.voice | F.video_note | F.audio)
async def handle_english_voice(message: types.Message, state: FSMContext, bot: Bot):
    """Обработка голосовых ответов пользователя в режиме живого английского."""
    voice_obj = message.voice or message.video_note or message.audio
    if not voice_obj:
        return

    await bot.send_chat_action(message.chat.id, "typing")
    status_msg = await message.answer("🎧 <i>Слушаю твою речь и анализирую произношение...</i>")

    try:
        file_info = await bot.get_file(voice_obj.file_id)
        audio_stream = io.BytesIO()
        await bot.download_file(file_info.file_path, destination=audio_stream)
        audio_bytes = audio_stream.getvalue()

        # Транскрибация через Gemini Multimodal
        transcribed_text = await transcribe_audio_gemini(audio_bytes)
        try:
            await status_msg.delete()
        except Exception:
            pass

        if not transcribed_text:
            await message.answer(
                "⚠️ Не удалось четко разобрать речь на аудио. Попробуй наговорить еще раз погромче или напиши текстом!"
            )
            return

        await message.answer(f"🗣 <b>Распознано:</b> <i>«{clean_telegram_html(transcribed_text)}»</i>")

        # Обрабатываем как ответ в диалоге с пометкой is_voice=True
        await process_english_input(message, state, transcribed_text, is_voice=True)

    except Exception as e:
        logger.error(f"Error handling english voice: {e}")
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer("⚠️ Произошла ошибка при обработке аудио. Напиши фразу текстом!")


# -------------------------------------------------------------
# 9. Обработка текстовых сообщений
# -------------------------------------------------------------
@router.message(ActiveModeStates.travel_english_mode, F.text)
async def handle_english_text(message: types.Message, state: FSMContext):
    """Обработка текстовых сообщений пользователя в режиме английского."""
    text = message.text.strip()

    # 1. Проверка на команду выхода
    if is_exit_command(text):
        await state.clear()
        await message.answer(
            "🏁 Вы вышли из режима «Живой English» в главное меню.",
            reply_markup=get_main_menu()
        )
        return

    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    except Exception:
        pass

    try:
        await process_english_input(message, state, text, is_voice=False)
    except Exception as e:
        logger.error(f"Error handling english text input: {e}", exc_info=True)
        await message.answer(
            "⚠️ Не удалось обработать ответ. Нажмите кнопку ниже или повторите фразу:",
            reply_markup=get_dialog_actions_keyboard()
        )


async def process_english_input(message: types.Message, state: FSMContext, user_text: str, is_voice: bool = False):
    """Единый процессинг ввода (текстового или транскрибированного голосового)."""
    data = await state.get_data()
    user_id = message.from_user.id
    current_scenario = data.get("current_scenario")
    awaiting_instant = data.get("awaiting_instant_translate", False)
    history = data.get("scenario_history", "")

    # Если сценарий не был выбран, но текст на английском — по умолчанию стартуем сценарий знакомства в баре
    if not current_scenario and not awaiting_instant:
        has_latin = bool(re.search(r"[a-zA-Z]{3,}", user_text))
        if has_latin:
            current_scenario = "bar_dating"
            await state.update_data(current_scenario="bar_dating")

    # Если включен режим мгновенного перевода или фраза явно вопросительная на русском
    is_translation_query = awaiting_instant or any(w in user_text.lower() for w in [
        "как сказать", "как по-английски", "переведи", "как будет", "как спросить"
    ])

    if is_translation_query or not current_scenario:
        # Режим мгновенного перевода на сленг
        await state.update_data(awaiting_instant_translate=False)
        res = await instant_translate_phrase(user_text)

        msg = (
            f"⚡️ <b>Разбор фразы для улицы и поездок:</b>\n"
            f"«<i>{clean_telegram_html(user_text)}</i>»\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"🤙 <b>1. Street Smart (Разговорный стандарт):</b>\n"
            f"• <b>{res['street_smart']}</b>\n"
            f"• 🗣 <i>Транскрипция: {res['street_transcription']}</i>\n\n"
            f"🔥 <b>2. Casual & Slang (Уличный сленг):</b>\n"
            f"• <b>{res['slang']}</b>\n"
            f"• 🗣 <i>Транскрипция: {res['slang_transcription']}</i>\n\n"
            f"🎩 <b>3. Polite (Вежливый вариант):</b>\n"
            f"• <b>{res['polite']}</b>\n"
            f"• 🗣 <i>Транскрипция: {res['polite_transcription']}</i>\n\n"
            f"💡 <b>Лайфхак:</b> {res['context_note']}"
        )

        add_user_xp(user_id, 5, is_correct=True)
        await send_clean_html(message, msg, reply_markup=get_dialog_actions_keyboard())
        return

    # Ролевой диалог с иностранцем
    sc_info = get_scenario_info(current_scenario)
    char_name = sc_info["character"]

    sim_result = await simulate_dialog_turn(
        user_id=user_id,
        scenario_key=current_scenario,
        user_message=user_text,
        history=history,
        is_voice=is_voice
    )

    # Обновляем историю диалога
    new_history = history + f"\nUser: {user_text}\nCharacter: {sim_result['character_reply_en']}"
    turns = data.get("turns", 0) + 1
    await state.update_data(scenario_history=new_history, turns=turns)
    increment_dialogs_count(user_id)

    # 1. Реплика персонажа
    reply_text = (
        f"👤 <b>{char_name}:</b>\n"
        f"«<b>{sim_result['character_reply_en']}</b>»\n"
        f"<i>({sim_result['character_reply_ru']})</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )

    # 2. Словарик полезных слов для базы
    vocab = sim_result.get("vocabulary", [])
    if vocab:
        reply_text += "📚 <b>Полезные слова раунда (для базы):</b>\n"
        for v in vocab:
            w = v.get("word", "")
            tr = v.get("transcription", "")
            tl = v.get("translation", "")
            reply_text += f"• <b>{w}</b> {tr} — <i>{tl}</i>\n"
        reply_text += "\n"

    # 3. Разбор учителя и грамматики
    score = sim_result.get("base_score", sim_result.get("native_score", 8))
    feedback = sim_result.get("teacher_feedback", sim_result.get("coach_tip", ""))
    better_phrase = sim_result.get("better_base_phrase", sim_result.get("better_native_phrase", ""))
    transcr = sim_result.get("phonetic_transcription_ru", "")

    reply_text += f"💡 <b>Разбор учителя:</b> ⭐️ <b>Оценка: {score}/10</b>\n"
    if feedback:
        reply_text += f"{feedback}\n\n"

    if better_phrase:
        reply_text += (
            f"✅ <b>Как сказать грамотно на базовом английском:</b>\n"
            f"• <b>{better_phrase}</b>\n"
        )
        if transcr:
            reply_text += f"• 🗣 <i>Транскрипция: {transcr}</i>\n"
        reply_text += "\n"

    # 4. Варианты продолжения диалога
    suggestions = sim_result.get("suggested_replies", [])
    if suggestions:
        reply_text += "🚀 <b>Что ты можешь ответить дальше (напиши или скажи голосом 🎙):</b>\n"
        for idx, s in enumerate(suggestions, 1):
            if isinstance(s, dict):
                en_txt = s.get("en", "")
                ru_txt = s.get("ru", "")
                s_tr = s.get("transcription", "")
                reply_text += f"{idx}. <b>«{en_txt}»</b>\n"
                if s_tr:
                    reply_text += f"   🗣 <i>{s_tr}</i>\n"
                if ru_txt:
                    reply_text += f"   — <i>{ru_txt}</i>\n"
            else:
                reply_text += f"{idx}. <b>«{s}»</b>\n"
        reply_text += "\n"

    reply_text += "💬 Напиши ответ текстом или <b>надиктуй голосом 🎙</b>!"

    # Сохраняем последние подсказки в state
    await state.update_data(last_suggestions=suggestions)
    await send_clean_html(message, reply_text, reply_markup=get_dialog_actions_keyboard())
