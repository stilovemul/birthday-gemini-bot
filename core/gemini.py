import os
import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from core.config import GEMINI_API_KEY

logger = logging.getLogger("GeminiEngine")

SYSTEM_INSTRUCTION = """Ты — персональный многофункциональный ИИ-ассистент Олега в Telegram (AiGemAntigravity).
Ты работаешь 24/7 автономно в облаке.
Твои качества:
- Дружелюбный, внимательный, эрудированный и полезный собеседник.
- Отвечай понятно, структурированно, грамотно и по делу на русском языке.
- Умеешь решать любые задачи: диалог, тексты, код, анализ фото, генерация идей, ответы на вопросы, помощь в делах.
"""

# Active models with maximum quota and instant fallback
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

user_chats: Dict[int, Any] = {}


def get_or_create_chat(user_id: int, model_name: str = CANDIDATE_MODELS[0]):
    c = get_genai_client()
    if user_id not in user_chats or user_chats[user_id].get("model") != model_name:
        chat = c.aio.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
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
                        system_instruction=SYSTEM_INSTRUCTION
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
