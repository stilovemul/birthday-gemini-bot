import io
import logging
import urllib.parse
import aiohttp
import time
import re
from typing import Optional, Tuple, Dict, Any
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("ImageGenerator")

# In-memory store for last generated prompts: {user_id: {"prompt": str, "timestamp": float}}
user_last_prompts: Dict[int, Dict[str, Any]] = {}


def set_last_image_prompt(user_id: int, prompt: str) -> None:
    user_last_prompts[user_id] = {
        "prompt": prompt.strip(),
        "timestamp": time.time()
    }


def get_last_image_info(user_id: int) -> Optional[Dict[str, Any]]:
    info = user_last_prompts.get(user_id)
    if info and (time.time() - info["timestamp"] < 900):  # 15 minutes window
        return info
    return None


def apply_heuristic_enrichment(raw_prompt: str) -> str:
    """Applies smart keyword translation and detail injection for Flux AI."""
    p_lower = raw_prompt.lower()
    tags = []

    if any(k in p_lower for k in ["девушк", "женщин", "красавиц", "модель", "girl", "woman"]):
        if any(r in p_lower for r in ["русск", "росси"]):
            tags.append("photorealistic portrait of a beautiful young Russian woman with natural makeup, clear detailed facial features, looking into camera, soft studio or outdoor lighting, 8k resolution, realistic skin texture, highly detailed, centered portrait photography")
        else:
            tags.append("photorealistic portrait of a gorgeous woman, clear detailed facial features, realistic eyes and hair, natural light, 8k, photorealistic photography")
    elif any(k in p_lower for k in ["парен", "мужчин", "человек", "man", "guy"]):
        tags.append("photorealistic portrait of a man, highly detailed facial features, realistic skin texture, cinematic lighting, 8k resolution photography")
    elif any(k in p_lower for k in ["кот", "кошк", "котен", "котик", "cat"]):
        tags.append("adorable cute cat, highly detailed fluffy fur, clear eyes, cinematic soft lighting, 8k masterpiece")
    elif any(k in p_lower for k in ["машин", "авто", "спорткар", "автомобил", "car"]):
        tags.append("sleek luxury sports car, dynamic angle, glossy paint reflection, cinematic lighting, 8k photorealistic")

    if any(k in p_lower for k in ["фото", "реальн", "реалистичн", "photo", "realistic"]):
        tags.append("raw 35mm photo, ultra-realistic, highly detailed, professional award-winning photograph")

    if tags:
        return f"{raw_prompt}, {', '.join(tags)}"
    return raw_prompt


async def translate_and_enrich_prompt(user_prompt: str) -> str:
    """
    Translates Russian prompt into rich, accurate English prompt optimized for Flux / SDXL.
    """
    enrich_system = """You are an expert AI prompt engineer for Flux and Stable Diffusion image models.
Translate the user's image request from Russian into a detailed, photorealistic English prompt.
CRITICAL RULES:
- If the user requests a person (e.g. Russian girl/woman, man, person), ensure the subject is CLEARLY PRESENT, centered portrait, detailed realistic face, natural skin texture, 8k resolution photo.
- Do NOT generate empty landscapes or roads if a human is requested!
- Output ONLY the final English prompt in 1-2 sentences."""

    c = get_genai_client()
    for model in CANDIDATE_MODELS:
        try:
            resp = await c.aio.models.generate_content(
                model=model,
                contents=f"User request: '{user_prompt}'\n\nOptimized English Prompt for Flux:",
                config={"system_instruction": enrich_system, "temperature": 0.3}
            )
            if resp and resp.text:
                cleaned = resp.text.strip().replace('"', '')
                logger.info(f"Enriched prompt via {model}: '{user_prompt}' -> '{cleaned}'")
                return cleaned
        except Exception as e:
            logger.warning(f"Model {model} failed for prompt enrichment: {e}")

    # Fallback to local heuristic enrichment
    return apply_heuristic_enrichment(user_prompt)


async def refine_prompt_with_ai(old_prompt: str, user_feedback: str) -> str:
    """
    Combines previous prompt with user's feedback into an updated prompt.
    """
    prompt_to_gemini = f"""Previous image prompt:
"{old_prompt}"

User feedback / complaint:
"{user_feedback}"

Generate a new detailed English diffusion prompt for Flux that directly fixes the complaint and fulfills what the user wanted.
If user says "тут нет девушки" or "где человек", make the person the prominent center subject with detailed face and photorealistic photography!
Output ONLY the resulting English prompt."""

    c = get_genai_client()
    for model in CANDIDATE_MODELS:
        try:
            resp = await c.aio.models.generate_content(
                model=model,
                contents=prompt_to_gemini
            )
            if resp and resp.text:
                refined = resp.text.strip().replace('"', '')
                logger.info(f"Refined prompt via {model}: '{refined}'")
                return refined
        except Exception as e:
            logger.warning(f"Model {model} failed for prompt refinement: {e}")

    # Fallback heuristic
    return apply_heuristic_enrichment(f"{old_prompt}, {user_feedback}")


async def generate_image_bytes(prompt: str, user_id: Optional[int] = None, is_already_en: bool = False) -> Tuple[bool, Optional[bytes], str, str]:
    """
    Generates image based on text prompt using high-speed Flux AI model.
    Returns (success, image_bytes, original_prompt, enriched_en_prompt).
    """
    clean_prompt = prompt.strip()
    if not clean_prompt:
        return False, None, "", "Укажите описание картинки."

    if not is_already_en:
        en_prompt = await translate_and_enrich_prompt(clean_prompt)
    else:
        en_prompt = clean_prompt

    if user_id:
        set_last_image_prompt(user_id, clean_prompt)

    encoded = urllib.parse.quote(en_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux&seed={int(time.time()*1000)%100000}"

    logger.info(f"Generating image via Flux for: '{en_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=50)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 5000:
                        logger.info(f"Image generated successfully ({len(data)} bytes)")
                        return True, data, clean_prompt, en_prompt
                    else:
                        return False, None, clean_prompt, "Сгенерированное изображение повреждено."
                else:
                    return False, None, clean_prompt, f"Ошибка генерации: HTTP {resp.status}"
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return False, None, clean_prompt, f"Ошибка генерации: {e}"
