import io
import logging
import urllib.parse
import aiohttp
from typing import Optional, Tuple, Dict
from core.gemini import get_genai_client

logger = logging.getLogger("ImageGenerator")

# In-memory store for last generated prompts: {user_id: prompt}
user_last_prompts: Dict[int, str] = {}


def set_last_image_prompt(user_id: int, prompt: str) -> None:
    user_last_prompts[user_id] = prompt.strip()


def get_last_image_prompt(user_id: int) -> Optional[str]:
    return user_last_prompts.get(user_id)


async def refine_prompt_with_ai(old_prompt: str, user_feedback: str) -> str:
    """
    Uses Gemini AI to combine previous image prompt and user's modification request into a refined prompt.
    """
    prompt_to_gemini = f"""Предыдущее описание сгенерированного изображения:
"{old_prompt}"

Пожелание пользователя по изменению/доработке:
"{user_feedback}"

Сформируй обновленный детальный промпт для генерации картинки (на русском или английском языке), в котором учтены правки пользователя и сохранен основной смысл.
Ответь ТОЛЬКО текстом промпта без кавычек, пояснений и лишних слов."""

    try:
        c = get_genai_client()
        resp = await c.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt_to_gemini
        )
        if resp and resp.text:
            refined = resp.text.strip().replace('"', '')
            logger.info(f"Refined prompt created: '{refined}' (from '{old_prompt}' + '{user_feedback}')")
            return refined
    except Exception as e:
        logger.error(f"Failed to refine prompt with Gemini: {e}")

    # Fallback combination
    return f"{old_prompt}, {user_feedback}"


async def generate_image_bytes(prompt: str, user_id: Optional[int] = None) -> Tuple[bool, Optional[bytes], str]:
    """
    Generates image based on text prompt using high-speed Flux AI model.
    Returns (success, image_bytes, info_message).
    """
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return False, None, "Укажите описание картинки, например: <code>/image кот космонавт на луне</code>"

    if user_id:
        set_last_image_prompt(user_id, clean_prompt)

    # URL-encode prompt for image generation endpoint
    encoded = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux"

    logger.info(f"Generating image for prompt: '{clean_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=50)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 5000:
                        logger.info(f"Image generated successfully ({len(data)} bytes)")
                        return True, data, clean_prompt
                    else:
                        return False, None, "Сгенерированное изображение повреждено или слишком маленькое."
                else:
                    return False, None, f"Ошибка сервиса генерации: HTTP {resp.status}"
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return False, None, f"Не удалось сгенерировать изображение: {e}"
