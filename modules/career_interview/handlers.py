"""
Обработчики специализированного тренажера собеседований для IT QA Manager (QA Lead / Head of QA).
"""

import io
import re
import html
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.voice_assistant.transcriber import transcribe_audio_gemini
from modules.career_interview.roles_catalog import INTERVIEW_ROLES, get_role_info
from modules.career_interview.keyboards import (
    get_interview_main_keyboard,
    get_interview_action_keyboard,
    get_tip_card_keyboard,
    get_post_scorecard_keyboard
)
from modules.career_interview.sparring import (
    conduct_interview_turn,
    generate_ideal_answer,
    generate_alternative_question,
    generate_final_scorecard
)
from modules.career_interview.formatter import send_clean_html, clean_telegram_html

logger = logging.getLogger("CareerInterviewHandlers")
router = Router(name="career_interview")


# -------------------------------------------------------------
# 1. Точка входа в режим собеседования QA Менеджера
# -------------------------------------------------------------
@router.message(Command("interview"))
@router.message(F.text.func(lambda t: bool(t and any(k in t.lower() for k in [
    "собеседование", "спарринг", "интервью", "тренажер интервью", "qa manager", "qa lead"
]))))
async def cmd_interview(message: types.Message, state: FSMContext):
    """Открывает главное меню симулятора собеседований IT QA Manager."""
    await state.set_state(ActiveModeStates.career_interview_mode)
    await state.update_data(
        interview_history="",
        role_key="",
        role_title="",
        current_question="",
        turns=0,
        awaiting_custom_role=False
    )

    welcome_text = (
        "🎙 <b>AI-Собеседование: IT QA Manager & Head of QA</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Ваш персональный симулятор собеседований топ-уровня на позиции <b>QA Lead / QA Manager / Head of QA</b>:\n\n"
        "• 🧪 <b>QA-Стратегия & Процессы</b>: Shift-Left, Quality Gates, пирамида тестов\n"
        "• 🤖 <b>Автоматизация & Стек</b>: архитектура AQA (Playwright, PyTest), CI/CD, flaky-тесты, нагрузка\n"
        "• 👥 <b>Команда & Найм</b>: грейды инженеров, мотивация SDET, конфликты с разработкой\n"
        "• 💥 <b>Факапы в проде & Релизы</b>: баги в продакшене, давление Product Owner, Post-Mortem (RCA)\n"
        "• 📊 <b>Бизнес & C-Level</b>: защита бюджета перед CTO, Defect Escape Rate, Cost of Quality\n"
        "• 🎯 <b>Торг об оффере QA</b>: зарплатная вилка 300k–500k+ ₽, KPI за стабильность\n"
        "• 🎙 <b>Поддержка голоса</b>: отвечайте текстом или надиктовывайте голосом!\n\n"
        "👇 <b>Выберите направление тренировки или введите свой QA-кейс:</b>"
    )

    # 1. Устанавливаем нижнюю компактную клавиатуру выхода
    await message.answer("Вход в режим «QA Собеседование»...", reply_markup=get_mode_keyboard("Собеседование QA"))
    # 2. Отправляем меню направлений с инлайн-кнопками
    await send_clean_html(message, welcome_text, reply_markup=get_interview_main_keyboard())


# -------------------------------------------------------------
# 2. Обработка выбора QA-направления
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("int_role_"))
async def cb_interview_role(callback: types.CallbackQuery, state: FSMContext):
    """Запуск собеседования по выбранной теме QA Менеджмента."""
    role_key = callback.data.replace("int_role_", "").strip()
    await state.set_state(ActiveModeStates.career_interview_mode)

    if role_key == "custom":
        await callback.answer()
        msg = (
            "✍️ <b>Напишите свой кейс, стек или тему для QA-собеседования:</b>\n\n"
            "<i>Например: «Переход с ручного тестирования на Playwright + TypeScript», "
            "«Внедрение Contract Testing (Pact) в микросервисной архитектуре», "
            "«Аудит процессов тестирования в FinTech», «Собеседование на Head of QA в e-commerce».</i>\n\n"
            "💬 Напишите текстом или <b>надиктуйте голосом 🎙</b> — я сразу начну симуляцию!"
        )
        await state.update_data(role_key="custom", role_title="Индивидуальный QA-кейс", awaiting_custom_role=True)
        await send_clean_html(callback, msg)
        return

    info = get_role_info(role_key)
    role_title = info["title"]
    opening_q = info["opening_question"]
    starter_tip = info["starter_tip"]

    await state.update_data(
        role_key=role_key,
        role_title=role_title,
        current_question=opening_q,
        turns=1,
        awaiting_custom_role=False,
        interview_history=f"Направление: {role_title}\nИнтервьюер (CTO): {opening_q}"
    )

    await callback.answer(f"Старт: {info['short_title']}...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    card_text = (
        f"{role_title} (Раунд #1)\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>Фокус оценки CTO / Head of Engineering:</b>\n{info['eval_focus']}\n\n"
        f"👔 <b>Интервьюер:</b> <i>«Здравствуйте! Давайте проверим ваш практический опыт руководства качеством.»</i>\n\n"
        f"❓ <b>ВОПРОС КАНДИДАТУ:</b>\n"
        f"<b>{opening_q}</b>\n\n"
        f"💡 <b>Подсказка эксперта:</b> <i>{starter_tip}</i>\n\n"
        f"👉 <i>Ответьте сообщением или надиктуйте ответ голосом 🎙:</i>"
    )

    await send_clean_html(callback, card_text, reply_markup=get_interview_action_keyboard(role_key))


# -------------------------------------------------------------
# 3. Интерактивные действия под вопросом
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("int_act_tip_"))
async def cb_interview_tip(callback: types.CallbackQuery, state: FSMContext):
    """Показывает эталонный ответ по модели STAR для QA Manager."""
    role_key = callback.data.replace("int_act_tip_", "").strip()
    data = await state.get_data()
    role_title = data.get("role_title") or get_role_info(role_key)["title"]
    current_q = data.get("current_question") or "Опишите ваш опыт в QA менеджменте."

    await callback.answer("Генерирую эталонный STAR-ответ...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    ideal = await generate_ideal_answer(callback.from_user.id, role_title, current_q)

    tip_text = (
        f"💡 <b>ЭТАЛОННЫЙ ОТВЕТ QA LEADER (Методология STAR):</b>\n"
        f"<i>{role_title}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"❓ <b>Вопрос:</b> «{current_q}»\n\n"
        f"📌 <b>S (Situation / Ситуация в проекте):</b>\n{ideal.get('situation', '')}\n\n"
        f"🎯 <b>T (Task / Моя задача как QA Lead):</b>\n{ideal.get('task', '')}\n\n"
        f"🛠 <b>A (Action / Мои действия и решения):</b>\n{ideal.get('action', '')}\n\n"
        f"📈 <b>R (Result / Бизнес-результат в цифрах):</b>\n{ideal.get('result', '')}\n\n"
        f"💎 <b>Стратегический вывод:</b>\n<i>«{ideal.get('takeaway', '')}»</i>\n\n"
        f"👉 <i>Теперь сформулируйте ваш собственный ответ текстом или голосом 🎙:</i>"
    )

    await send_clean_html(callback, tip_text, reply_markup=get_tip_card_keyboard(role_key))


@router.callback_query(F.data.startswith("int_act_skip_"))
async def cb_interview_skip(callback: types.CallbackQuery, state: FSMContext):
    """Генерирует альтернативный глубокий кейс по QA менеджменту."""
    role_key = callback.data.replace("int_act_skip_", "").strip()
    data = await state.get_data()
    role_title = data.get("role_title") or get_role_info(role_key)["title"]
    history = data.get("interview_history", "")
    turns = data.get("turns", 1) + 1

    await callback.answer("Подбираю альтернативный QA-кейс...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    res = await generate_alternative_question(callback.from_user.id, role_title, history=history)
    new_q = res.get("next_tough_question", "")
    reaction = res.get("interviewer_reaction", "Сменим ракурс вопроса.")
    tip = res.get("pro_tip", "")

    new_history = f"{history}\nИнтервьюер (новый кейс): {new_q}"
    await state.update_data(
        current_question=new_q,
        turns=turns,
        interview_history=new_history[-2000:]
    )

    card_text = (
        f"{role_title} (Раунд #{turns})\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"👔 <b>Интервьюер:</b> <i>«{reaction}»</i>\n\n"
        f"❓ <b>НОВЫЙ КЕЙС-ВОПРОС:</b>\n"
        f"<b>{new_q}</b>\n\n"
        f"💡 <b>Подсказка:</b> <i>{tip}</i>\n\n"
        f"👉 <i>Ответьте сообщением или надиктуйте ответ голосом 🎙:</i>"
    )

    await send_clean_html(callback, card_text, reply_markup=get_interview_action_keyboard(role_key))


@router.callback_query(F.data.startswith("int_act_finish_"))
async def cb_interview_finish(callback: types.CallbackQuery, state: FSMContext):
    """Подведение итогов собеседования и выдача QA Manager Scorecard."""
    role_key = callback.data.replace("int_act_finish_", "").strip()
    data = await state.get_data()
    role_title = data.get("role_title") or get_role_info(role_key)["title"]
    history = data.get("interview_history", "")

    await callback.answer("Формирую итоговую аттестацию QA Scorecard...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    scorecard = await generate_final_scorecard(callback.from_user.id, role_title, history=history)

    strengths = "\n".join([f"• {s}" for s in scorecard.get("top_strengths", [])])
    growth = "\n".join([f"• {g}" for g in scorecard.get("growth_areas", [])])

    report_text = (
        f"📊 <b>ИТОГОВЫЙ SCORECARD: IT QA MANAGER</b>\n"
        f"<i>Направление: {role_title}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 <b>Итоговый балл:</b> <b>{scorecard.get('final_score', '8.5/10')}</b>\n"
        f"🎯 <b>Вердикт наемного комитета:</b>\n<b>{scorecard.get('verdict', '🟢 Рекомендован к офферу')}</b>\n\n"
        f"📈 <b>Компетенции руководителя QA:</b>\n"
        f"▫️ <b>QA-Стратегия & Процессы:</b> {scorecard.get('qa_strategy_rating', '9/10')}\n"
        f"▫️ <b>AQA & Технический стек:</b> {scorecard.get('aqa_tech_rating', '8/10')}\n"
        f"▫️ <b>Лидерство & Управление:</b> {scorecard.get('leadership_rating', '8/10')}\n"
        f"▫️ <b>Бизнес-метрики & Риски:</b> {scorecard.get('business_metrics_rating', '8/10')}\n\n"
        f"💪 <b>Главные сильные стороны:</b>\n{strengths}\n\n"
        f"⚠️ <b>Зоны роста до реального оффера:</b>\n{growth}\n\n"
        f"🚀 <b>Золотой совет для оффера:</b>\n<i>«{scorecard.get('golden_advice', '')}»</i>"
    )

    await send_clean_html(callback, report_text, reply_markup=get_post_scorecard_keyboard())


@router.callback_query(F.data == "int_act_roles")
async def cb_interview_back_to_roles(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору направлений QA."""
    await callback.answer()
    text = "👇 <b>Выберите тему для новой тренировки QA Менеджера:</b>"
    await send_clean_html(callback, text, reply_markup=get_interview_main_keyboard())


# -------------------------------------------------------------
# 4. Обработка текстовых сообщений кандидата
# -------------------------------------------------------------
@router.message(ActiveModeStates.career_interview_mode, F.text)
async def handle_interview_text(message: types.Message, state: FSMContext):
    """Обрабатывает ответ кандидата или ввод индивидуального QA-кейса."""
    raw_text = message.text.strip()

    # 1. Проверка команды выхода
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «QA Собеседование» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    data = await state.get_data()
    role_key = data.get("role_key", "custom")
    role_title = data.get("role_title", "")
    history = data.get("interview_history", "")
    turns = data.get("turns", 0)

    # 2. Быстрые текстовые триггеры
    t_lower = raw_text.lower()
    if any(k in t_lower for k in ["другой вопрос", "смени вопрос", "пропустить", "следующий кейс", "следующий вопрос"]):
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        res = await generate_alternative_question(message.from_user.id, role_title or "QA Manager", history=history)
        new_q = res.get("next_tough_question", "")
        await state.update_data(current_question=new_q, turns=turns + 1)
        card_text = (
            f"🔄 <b>Новый кейс по теме {role_title}:</b>\n\n"
            f"❓ <b>{new_q}</b>\n\n"
            f"💡 <i>{res.get('pro_tip', '')}</i>"
        )
        await send_clean_html(message, card_text, reply_markup=get_interview_action_keyboard(role_key))
        return

    if any(k in t_lower for k in ["итог", "оценка", "завершить", "scorecard", "результат", "аттестация"]):
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        scorecard = await generate_final_scorecard(message.from_user.id, role_title or "QA Manager", history=history)
        strengths = "\n".join([f"• {s}" for s in scorecard.get("top_strengths", [])])
        growth = "\n".join([f"• {g}" for g in scorecard.get("growth_areas", [])])
        report_text = (
            f"📊 <b>ИТОГОВЫЙ SCORECARD: IT QA MANAGER</b>\n\n"
            f"🏆 <b>Балл:</b> {scorecard.get('final_score', '8.5/10')}\n"
            f"🎯 <b>Вердикт:</b> {scorecard.get('verdict', '🟢 Рекомендован к офферу')}\n\n"
            f"💪 <b>Сильные стороны:</b>\n{strengths}\n\n"
            f"⚠️ <b>Точки роста:</b>\n{growth}\n\n"
            f"🚀 <b>Совет:</b> <i>«{scorecard.get('golden_advice', '')}»</i>"
        )
        await send_clean_html(message, report_text, reply_markup=get_post_scorecard_keyboard())
        return

    # 3. Ввод индивидуального QA-кейса / ситуации
    if data.get("awaiting_custom_role") or not role_title:
        custom_case = raw_text
        role_title = f"🧪 {custom_case}"
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        # Генерируем первый глубокий вопрос для кастомного QA-кейса
        res = await conduct_interview_turn(
            message.from_user.id,
            f"Кандидат на позицию IT QA Manager хочет разобрать кейс: «{custom_case}». Задай первый глубокий вопрос от лица CTO для проверки архитектурной и управленческой зрелости.",
            role_title=custom_case,
            history=""
        )
        first_q = res.get("next_tough_question", f"Как вы опишете стратегию решения задачи «{custom_case}»?")
        tip = res.get("pro_tip", "Отвечайте структурированно по методологии STAR.")

        await state.update_data(
            role_key="custom",
            role_title=role_title,
            current_question=first_q,
            turns=1,
            awaiting_custom_role=False,
            interview_history=f"Кейс QA: {role_title}\nИнтервьюер (CTO): {first_q}"
        )

        card_text = (
            f"🎯 <b>QA-Собеседование: {custom_case}</b> (Раунд #1)\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"👔 <b>Интервьюер (CTO):</b> <i>«Отличная тема. Давайте проверим ваше видение как руководителя качества.»</i>\n\n"
            f"❓ <b>ВОПРОС КАНДИДАТУ:</b>\n"
            f"<b>{first_q}</b>\n\n"
            f"💡 <b>Подсказка эксперта:</b> <i>{tip}</i>\n\n"
            f"👉 <i>Ответьте сообщением или надиктуйте ответ голосом 🎙:</i>"
        )
        await send_clean_html(message, card_text, reply_markup=get_interview_action_keyboard("custom"))
        return

    # 4. Стандартный раунд: ответ кандидата на вопрос интервьюера
    await _process_candidate_answer(message, state, raw_text, is_voice=False)


# -------------------------------------------------------------
# 5. Обработка голосовых сообщений и кружочков кандидата
# -------------------------------------------------------------
@router.message(ActiveModeStates.career_interview_mode, F.voice)
async def handle_interview_voice(message: types.Message, state: FSMContext):
    """Обрабатывает голосовой ответ кандидата через Gemini Multimodal Audio."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        file = await message.bot.get_file(message.voice.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        text = await transcribe_audio_gemini(buf.getvalue(), mime_type="audio/ogg")
    except Exception as e:
        logger.error(f"Error transcribing voice in QA interview: {e}")
        text = None

    if not text:
        await message.answer("🎙 <i>Не удалось разобрать голосовое сообщение. Пожалуйста, повторите фразу или напишите текстом.</i>", parse_mode=ParseMode.HTML)
        return

    await message.answer(f"🎤 <b>Ваш голосовой ответ:</b> «<i>{html.escape(text)}</i>»", parse_mode=ParseMode.HTML)
    await _process_candidate_answer(message, state, text, is_voice=True)


@router.message(ActiveModeStates.career_interview_mode, F.video_note)
async def handle_interview_video_note(message: types.Message, state: FSMContext):
    """Обрабатывает видеосообщение (кружочек) кандидата."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        file = await message.bot.get_file(message.video_note.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        text = await transcribe_audio_gemini(buf.getvalue(), mime_type="video/mp4")
    except Exception as e:
        logger.error(f"Error transcribing video note in QA interview: {e}")
        text = None

    if not text:
        await message.answer("📹 <i>Не удалось разобрать речь в видеосообщении. Пожалуйста, повторите фразу.</i>", parse_mode=ParseMode.HTML)
        return

    await message.answer(f"📹 <b>Ваш видеоответ:</b> «<i>{html.escape(text)}</i>»", parse_mode=ParseMode.HTML)
    await _process_candidate_answer(message, state, text, is_voice=True)


@router.message(ActiveModeStates.career_interview_mode, F.audio)
async def handle_interview_audio(message: types.Message, state: FSMContext):
    """Обрабатывает аудиофайлы кандидата."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        file = await message.bot.get_file(message.audio.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        mime = message.audio.mime_type or "audio/mpeg"
        text = await transcribe_audio_gemini(buf.getvalue(), mime_type=mime)
    except Exception as e:
        logger.error(f"Error transcribing audio in QA interview: {e}")
        text = None

    if not text:
        await message.answer("🎵 <i>Не удалось разобрать речь в аудиофайле. Пожалуйста, повторите фразу.</i>", parse_mode=ParseMode.HTML)
        return

    await message.answer(f"🎙 <b>Распознанный ответ:</b> «<i>{html.escape(text)}</i>»", parse_mode=ParseMode.HTML)
    await _process_candidate_answer(message, state, text, is_voice=True)


# -------------------------------------------------------------
# 6. Вспомогательная функция проведения раунда QA-собеседования
# -------------------------------------------------------------
async def _process_candidate_answer(
    message: types.Message,
    state: FSMContext,
    candidate_text: str,
    is_voice: bool = False
):
    """Анализирует ответ кандидата с позиций CTO / Head of Engineering и рендерит карточку."""
    data = await state.get_data()
    role_key = data.get("role_key", "custom")
    role_title = data.get("role_title", "IT QA Manager")
    history = data.get("interview_history", "")
    turns = data.get("turns", 1) + 1

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    res = await conduct_interview_turn(
        user_id=message.from_user.id,
        user_reply=candidate_text,
        role_title=role_title,
        history=history,
        is_voice=is_voice
    )

    feedback = res.get("feedback_on_previous", "")
    reaction = res.get("interviewer_reaction", "Понял вашу логику.")
    next_q = res.get("next_tough_question", "Как вы решите следующий кейс?")
    tip = res.get("pro_tip", "")
    score = res.get("score", "8/10")

    # Обновляем историю в FSM
    new_hist = f"{history}\nКандидат QA ({'голос' if is_voice else 'текст'}): {candidate_text}\nИнтервьюер (оценка {score}): {next_q}"
    await state.update_data(
        current_question=next_q,
        turns=turns,
        interview_history=new_hist[-2500:]
    )

    card_lines = [
        f"{role_title} (Раунд #{turns})",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"📊 <b>Разбор ответа (QA Leadership & STAR):</b>",
        f"⭐️ <b>Оценка ответа:</b> <b>{score}</b>",
        f"{feedback}\n",
        f"👔 <b>Интервьюер (CTO):</b> <i>«{reaction}»</i>\n",
        f"❓ <b>СЛЕДУЮЩИЙ ВОПРОС / КЕЙС:</b>",
        f"<b>{next_q}</b>\n"
    ]

    if tip:
        card_lines.append(f"💡 <b>Подсказка эксперта:</b>\n<i>{tip}</i>\n")

    card_lines.append("👉 <i>Ответьте сообщением или надиктуйте ответ голосом 🎙:</i>")

    await send_clean_html(
        message,
        "\n".join(card_lines),
        reply_markup=get_interview_action_keyboard(role_key)
    )
