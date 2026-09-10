"""
AI-движок ролевого тренажера и мгновенного перевода «🗣 Живой English»:
- Отыгрыш персонажей в реальных бытовых ситуациях
- Оценка естественности ответа (Native Score 1-10)
- Подсказки, как сказать фразу на 100% живом сленге нейтивов
- Русская транскрипция с ударениями для идеального произношения
- Мгновенный перевод на 3 стиля: Street Smart, Polite, Slang.
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import get_genai_client, CANDIDATE_MODELS
from modules.travel_english.scenarios_catalog import get_scenario_info

logger = logging.getLogger("TravelEnglishSimulator")


async def simulate_dialog_turn(
    user_id: int,
    scenario_key: str,
    user_message: str,
    history: str = "",
    is_voice: bool = False
) -> Dict[str, Any]:
    """
    Проводит один раунд интерактивного диалога:
    - Собеседник отвечает на чистом, понятном, базовом школьном английском (A2-B1)
    - БЕЗ сложного сленга и идиом
    - Разбирает полезные слова из реплики для пополнения словарного запаса
    - Дает 3 простых и понятных варианта ответа с переводом и транскрипцией
    - Мягко исправляет грамматические неточности
    """
    sc_info = get_scenario_info(scenario_key)
    char_name = sc_info["character"]
    situation = sc_info["situation"]

    system_prompt = f"""Ты — заботливый, дружелюбный преподаватель английского языка и собеседник в ролевой игре.
Ученик попросил: "СТРОГО БЕЗ СЛОЖНОГО СЛЕНГА! Чистый, понятный школьный английский (уровни Elementary / Pre-Intermediate / Intermediate A1-B1), чтобы подтянуть базу, слова и порядок слов".

Сейчас идет ролевая игра:
Ситуация: {situation}
Твоя роль персонажа: {char_name} ({sc_info['character_role']}).

Текущий ответ ученика: "{user_message}"
Ученик ответил голосом: {"Да (голосовое сообщение)" if is_voice else "Нет (текст)"}.

Правила генерации ответа:
1. "character_reply_en": твоя реплика как персонажа на ПРОСТОМ, ПРАВИЛЬНОМ и ПОНЯТНОМ базовом английском (1-3 коротких предложения). Никакого сложного сленга! Обязательно закончи встречным простым вопросом, чтобы диалог продолжался.
2. "character_reply_ru": точный понятный перевод твоей реплики на русский язык.
3. "base_score": оценка ответа ученика по 10-балльной шкале (1-10) за понятность и базовую грамматику.
4. "vocabulary": массив из 2-3 полезных базовых слов или словосочетаний из твоей реплики: {{"word": "...", "transcription": "[...]", "translation": "..."}} для пополнения словарного запаса ученика.
5. "better_base_phrase": как выразить мысль ученика на правильном, чистом базовом английском без ошибок.
6. "phonetic_transcription_ru": русская транскрипция фразы с ударениями для легкого чтения.
7. "teacher_feedback": ободряющий, доброжелательный комментарий преподавателя на русском (1-2 предложения): похвалить за смелость, подсказать базовое грамматическое правило (например: глагол to be, Present Simple, правильный предлог).
8. "suggested_replies": массив из 3 простых вариантов ответа для ученика на чистом базовом английском:
   [{{"en": "...", "ru": "...", "transcription": "[...]"}}]

Верни СТРОГО валидный JSON:
{{
  "character_reply_en": "...",
  "character_reply_ru": "...",
  "base_score": 9,
  "vocabulary": [
    {{"word": "...", "transcription": "[...]", "translation": "..."}}
  ],
  "better_base_phrase": "...",
  "phonetic_transcription_ru": "[...]",
  "teacher_feedback": "...",
  "suggested_replies": [
    {{"en": "...", "ru": "...", "transcription": "[...]"}},
    {{"en": "...", "ru": "...", "transcription": "[...]"}},
    {{"en": "...", "ru": "...", "transcription": "[...]"}}
  ]
}}
"""

    user_prompt = f"""История диалога:\n{history}\n\nУченик сказал: {user_message}"""

    client = get_genai_client()
    for model_name in CANDIDATE_MODELS:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.5,
                    "response_mime_type": "application/json"
                }
            )
            if resp and resp.text:
                cleaned = resp.text.strip()
                m = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    return data
        except Exception as e:
            logger.warning(f"Model {model_name} error in travel english simulator ({e}), trying next...")

    # Фолбэк на базовом английском
    return {
        "character_reply_en": "Nice to meet you! I like this music. What do you like to do on weekends?",
        "character_reply_ru": "Приятно познакомиться! Мне нравится эта музыка. А чем ты любишь заниматься по выходным?",
        "base_score": 8,
        "vocabulary": [
            {"word": "nice to meet you", "transcription": "[найс ту мит ю]", "translation": "приятно познакомиться"},
            {"word": "weekends", "transcription": "[уи́к-эндз]", "translation": "выходные дни"}
        ],
        "better_base_phrase": "Nice to meet you! My name is Oleg, I am from Saint Petersburg.",
        "phonetic_transcription_ru": "[Найс ту мит ю! Май нэйм из Оле́г, ай эм фром Сэйнт Пи́терсберг]",
        "teacher_feedback": "Отличное начало! Фраза простая и всем понятная. Не забывай улыбаться при знакомстве!",
        "suggested_replies": [
            {"en": "I like to travel and spend time outdoors.", "ru": "Я люблю путешествовать и проводить время на природе.", "transcription": "[Ай лайк ту трэ́вл энд спэнд тайм а́утдорс]"},
            {"en": "I usually relax and watch movies with friends.", "ru": "Я обычно отдыхаю и смотрю фильмы с друзьями.", "transcription": "[Ай ю́жуэли рилэ́кс энд уотч му́виз уиз фрэндз]"},
            {"en": "I enjoy sports and good food. What about you?", "ru": "Мне нравится спорт и вкусная еда. А тебе?", "transcription": "[Ай инджо́й спортс энд гуд фуд. Уот эба́ут ю?]"}
        ]
    }


async def instant_translate_phrase(user_query: str) -> Dict[str, Any]:
    """
    Раскладывает любую русскую фразу или вопрос пользователя на 3 стиля живого английского:
    1. Street Smart (естественный разговорный)
    2. Polite (вежливый)
    3. Slang (уличный сленг)
    """
    system_prompt = """Ты — эксперт по разговорному английскому и сленгу нейтивов.
Пользователь спрашивает, как сказать фразу по-английски в реальной жизни или путешествии.
Никакой грамматики и скучных лекций! Только реальный язык.

Ты должен дать:
1. "street_smart": самый органичный, разговорный вариант, как говорят 90% нейтивов.
2. "street_transcription": русская транскрипция с ударениями для street_smart.
3. "polite": вежливый вариант для деликатных ситуаций.
4. "polite_transcription": русская транскрипция для polite.
5. "slang": яркий разговорный сленг/сокращение.
6. "slang_transcription": русская транскрипция для slang.
7. "context_note": короткий лайфхак, где какая фраза уместна.

Верни СТРОГО валидный JSON:
{
  "street_smart": "...",
  "street_transcription": "[...]",
  "polite": "...",
  "polite_transcription": "[...]",
  "slang": "...",
  "slang_transcription": "[...]",
  "context_note": "..."
}
"""

    client = get_genai_client()
    for model_name in CANDIDATE_MODELS:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=f"Как сказать: {user_query}",
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.5,
                    "response_mime_type": "application/json"
                }
            )
            if resp and resp.text:
                cleaned = resp.text.strip()
                m = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if m:
                    return json.loads(m.group(0))
        except Exception as e:
            logger.warning(f"Model {model_name} failed in instant translator ({e}), trying next...")

    return {
        "street_smart": "Can you do better on the price, please?",
        "street_transcription": "[Кэн ю ду бэ́тер он зэ прайс, плиз?]",
        "polite": "Could you possibly offer a small discount on this?",
        "polite_transcription": "[Куд ю по́сибли о́фер э смол ди́скаунт он зис?]",
        "slang": "Can you do 20 bucks cash right now?",
        "slang_transcription": "[Кэн ю ду туэ́нти бакс кэш райт нау?]",
        "context_note": "Фраза со словом 'cash' работает безотказно на любых рынках мира!"
    }
