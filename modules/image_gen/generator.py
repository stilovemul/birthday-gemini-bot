import io
import logging
import urllib.parse
import aiohttp
from typing import Optional, Tuple

logger = logging.getLogger("ImageGenerator")


async def generate_image_bytes(prompt: str, enhance_prompt: bool = True) -> Tuple[bool, Optional[bytes], str]:
    """
    Generates image based on text prompt using high-speed Flux / SDXL AI model.
    Returns (success, image_bytes, info_message).
    """
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return False, None, "Укажите описание картинки, например: <code>/image кот космонавт на луне</code>"

    # URL-encode prompt for image generation endpoint
    encoded = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux"

    logger.info(f"Generating image for prompt: '{clean_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=45)) as resp:
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
