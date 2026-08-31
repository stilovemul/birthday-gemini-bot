import logging
from typing import Optional
from google import genai
from google.genai import types
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("VoiceTranscriber")


async def transcribe_audio_gemini(audio_bytes: bytes, mime_type: str = "audio/ogg") -> Optional[str]:
    """
    Transcribes audio bytes to Russian text using Gemini Multimodal Audio Perception.
    """
    c = get_genai_client()
    prompt = (
        "Ты — высокоточный профессиональный транскрибатор речи. "
        "Внимательно прослушай эту аудиозапись и дословно переведи речь в текст на русском языке. "
        "Исправь очевидные оговорки в названиях команд (умный дом, напоминания, еда, погода). "
        "Верни ТОЛЬКО распознанный текст без кавычек, комментариев и мета-сообщений."
    )

    contents = [
        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        prompt
    ]

    for model_name in CANDIDATE_MODELS:
        try:
            response = await c.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1000
                )
            )
            if response and response.text:
                result = response.text.strip().strip('"').strip("'")
                if result:
                    logger.info(f"Audio successfully transcribed via {model_name}: '{result}'")
                    return result
        except Exception as e:
            logger.warning(f"Voice transcription with model {model_name} failed: {e}. Trying fallback...")

    return None
