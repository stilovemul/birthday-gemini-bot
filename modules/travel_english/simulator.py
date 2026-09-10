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
    Проводит один раунд ролевого диалога с иностранцем:
    1. Иностранец отвечает в рамках ситуации на живом разговорном английском.
    2. Тренер дает разбор: Native Score (1-10), лучшую версию фразы, русскую транскрипцию и советы.
    """
    sc_info = get_scenario_info(scenario_key)
    char_name = sc_info["character"]
    situation = sc_info["situation"]

    system_prompt = f"""Ты — первоклассный носитель языка (Native Speaker) и персональный коуч по уличному разговорному английскому (Street Smart English).
Никакой занудной академической школьной грамматики! Твоя цель — научить туриста говорить свободно, естественно и без стеснения, как говорят современные американцы и британцы в путешествиях.

Сейчас идет ролевая игра:
Ситуация: {situation}
Твоя роль персонажа: {char_name} ({sc_info['character_role']}).

Текущий ответ пользователя (ученика): "{user_message}"
Пользователь ответил голосом: {"Да" if is_voice else "Нет (текст)"}.

Инструкция к генерации JSON-ответа:
1. "character_reply_en": твоя реплика как персонажа на живом естественном английском (1-3 коротких предложения).
2. "character_reply_ru": перевод твоей реплики на русский язык в скобках.
3. "native_score": оценка фразы пользователя по шкале от 1 до 10 (где 10 — звучит как стопроцентный нейтив, 5 — понятно, но книжно/по-русски).
4. "better_native_phrase": как эту же мысль выразил бы реальный американец/британец на улице (живой сленг, сокращения: "Can I grab...", "I'm good", "No worries").
5. "phonetic_transcription_ru": транскрипция лучшей фразы РУССКИМИ БУКВАМИ с ударениями для легкого чтения, например: "[Кэн ай грэб эн а́йст ла́тэ ту го́у, плиз?]".
6. "coach_tip": короткий, яркий и дружелюбный совет от тренера (1-2 предложения): в чем была ошибка или почему именно так звучит круче.
7. "suggested_replies": массив из 2-3 вариантов фраз на английском, которыми пользователь может ответить дальше на твою реплику.

Верни СТРОГО валидный JSON следующего формата:
{{
  "character_reply_en": "...",
  "character_reply_ru": "...",
  "native_score": 8,
  "better_native_phrase": "...",
  "phonetic_transcription_ru": "[...]",
  "coach_tip": "...",
  "suggested_replies": ["...", "..."]
}}
"""

    user_prompt = f"""История диалога:\n{history}\n\nПользователь сказал: {user_message}"""

    client = get_genai_client()
    for model_name in CANDIDATE_MODELS:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "temperature": 0.6,
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

    # Фолбэк на случай сбоя
    return {
        "character_reply_en": "Gotcha, absolutely! Anything else I can get you?",
        "character_reply_ru": "Понял тебя, без проблем! Что-то еще для тебя?",
        "native_score": 7,
        "better_native_phrase": "Can I grab this to go, please?",
        "phonetic_transcription_ru": "[Кэн ай грэб зис ту го́у, плиз?]",
        "coach_tip": "Используй глагол «grab» вместо книжного «order» или «want» — это звучит максимально по-нейтивски!",
        "suggested_replies": [
            "No, that's all, thanks! How much is it?",
            "Can I pay by card or contactless?",
            "Keep the change, cheers!"
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
