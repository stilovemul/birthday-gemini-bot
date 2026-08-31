import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from core.config import GEMINI_API_KEY, MSK_TZ, DATA_DIR

logger = logging.getLogger("GeminiEngine")

CANDIDATE_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash"
]

client = None


def get_genai_client():
    global client
    if client is None:
        api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        client = genai.Client(api_key=api_key)
    return client


def get_dynamic_context() -> str:
    """Loads user's birthdays and reminders to keep Gemini always aware of personal context."""
    now_msk = datetime.now(MSK_TZ).strftime("%d.%m.%Y %H:%M (%A, MSK UTC+3)")
    
    # Load Birthdays
    birthdays_str = ""
    b_file = DATA_DIR / "birthdays.json"
    if b_file.exists():
        try:
            with open(b_file, "r", encoding="utf-8") as f:
                b_list = json.load(f)
                b_lines = []
                for b in b_list:
                    name = b.get("name", "")
                    d = b.get("day")
                    m = b.get("month")
                    y = b.get("year", "")
                    y_str = f" ({y} г.р.)" if y else ""
                    b_lines.append(f"• {name}: {d:02d}.{m:02d}{y_str}")
                birthdays_str = "\n".join(b_lines)
        except Exception as e:
            logger.warning(f"Error reading birthdays context: {e}")

    ctx = (
        f"Текущая дата и время: {now_msk}.\n"
        f"Пользователь: Олег (Telegram).\n\n"
        f"Список сохраненных дней рождения близких Олега:\n"
        f"{birthdays_str if birthdays_str else 'Список пока пуст'}\n\n"
        "Когда Олег спрашивает про дни рождения близких (мамы, папы, жены, брата или друзей), всегда точно отвечай дату, сколько лет исполняется и сколько дней осталось."
    )
    return ctx


def get_system_instruction() -> str:
    ctx = get_dynamic_context()
    return f"""Ты — персональный многофункциональный ИИ-ассистент Олега в Telegram (AiGemAntigravity).
Ты работаешь 24/7 автономно в облаке.

{ctx}

Твои качества:
- Дружелюбный, внимательный, эрудированный и полезный собеседник.
- Отвечай понятно, структурированно, грамотно и по делу на русском языке.
- Умеешь решать любые задачи: диалог, поиск дней рождения, расчеты, тексты, код, анализ фото, помощь в делах.
"""


user_chats: Dict[int, Any] = {}


def get_or_create_chat(user_id: int, model_name: str = CANDIDATE_MODELS[0]):
    c = get_genai_client()
    sys_inst = get_system_instruction()
    if user_id not in user_chats or user_chats[user_id].get("model") != model_name:
        chat = c.aio.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
                temperature=0.7
            )
        )
        user_chats[user_id] = {"model": model_name, "chat": chat}
    return user_chats[user_id]["chat"]


def reset_chat_session(user_id: int):
    if user_id in user_chats:
        del user_chats[user_id]


async def ask_gemini(user_id: int, prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> str:
    c = get_genai_client()
    sys_inst = get_system_instruction()
    
    for model_name in CANDIDATE_MODELS:
        try:
            if image_bytes:
                contents = [
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt or "Что изображено на этом фото? Опиши подробно."
                ]
                response = await c.aio.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_inst
                    )
                )
                if response and response.text:
                    return response.text.strip()
            else:
                chat = get_or_create_chat(user_id, model_name)
                response = await chat.send_message(prompt)
                if response and response.text:
                    return response.text.strip()
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}. Trying next candidate...")
            reset_chat_session(user_id)

    return "⏳ <b>Нейросеть Gemini сейчас испытывает кратковременную нагрузку.</b>\nПожалуйста, отправьте сообщение через 15 секунд — я сразу отвечу!"
