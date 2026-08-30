import io
import logging
import urllib.parse
import aiohttp
import time
import re
from typing import Optional, Tuple, Dict, Any
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("ImageGenerator")

# In-memory store for last generated prompts: {user_id: {"prompt": str, "en_prompt": str, "timestamp": float}}
user_last_prompts: Dict[int, Dict[str, Any]] = {}

# In-memory store for user engine preference: {user_id: "flux" | "turbo" | "flux-anime" | "flux-3d"}
user_engines: Dict[int, str] = {}

# Active prompt awaiting mode: {user_id: True}
user_awaiting_image_prompt: Dict[int, bool] = {}


def set_user_awaiting_image(user_id: int, status: bool = True) -> None:
    user_awaiting_image_prompt[user_id] = status


def is_user_awaiting_image(user_id: int) -> bool:
    return user_awaiting_image_prompt.get(user_id, False)


def set_user_engine(user_id: int, engine: str) -> None:
    user_engines[user_id] = engine


def get_user_engine(user_id: int) -> str:
    return user_engines.get(user_id, "flux")


def set_last_image_prompt(user_id: int, prompt: str, en_prompt: str = "") -> None:
    user_last_prompts[user_id] = {
        "prompt": prompt.strip(),
        "en_prompt": en_prompt.strip(),
        "timestamp": time.time()
    }


def get_last_image_info(user_id: int) -> Optional[Dict[str, Any]]:
    info = user_last_prompts.get(user_id)
    if info and (time.time() - info["timestamp"] < 900):  # 15 minutes window
        return info
    return None


def apply_heuristic_enrichment(raw_prompt: str) -> str:
    """Applies pure photography tokens with authentic Slavic features without anime bleeding."""
    p_lower = raw_prompt.lower()
    tags = []

    if any(k in p_lower for k in ["девушк", "женщин", "красавиц", "модель", "girl", "woman"]):
        if any(r in p_lower for r in ["русск", "росси", "славян"]):
            tags.append("candid 35mm portrait photography of a beautiful 23-year-old natural Slavic Russian woman with authentic Slavic facial features, light brown hair, natural skin texture, authentic human eyes and smile, soft daylight, high resolution real photograph")
        else:
            tags.append("candid 35mm portrait photography of a beautiful natural woman, authentic human features, natural daylight, real photograph")
    elif any(k in p_lower for k in ["парен", "мужчин", "человек", "man", "guy"]):
        tags.append("candid portrait photograph of a man, authentic human facial features, natural lighting, real photography")
    elif any(k in p_lower for k in ["кот", "кошк", "котен", "котик", "cat"]):
        tags.append("adorable realistic cat, fluffy fur, natural daylight, real pet photography")
    elif any(k in p_lower for k in ["машин", "авто", "спорткар", "автомобил", "car"]):
        tags.append("real-life automotive photography of a sleek sports car, glossy reflections, natural ambient daylight, 8k raw photo")

    if any(k in p_lower for k in ["постел", "кроват", "утром", "утро", "bed", "morning"]):
        tags.append("relaxing in cozy white morning bed sheets, soft morning natural sunlight from bedroom window, peaceful authentic lifestyle photo")

    if tags:
        return f"{', '.join(tags)}"
    return f"{raw_prompt}, candid 35mm photography, natural lighting, authentic real life photo"


async def translate_and_enrich_prompt(user_prompt: str) -> str:
    """
    Translates Russian prompt into clean, photorealistic English photography prompt.
    """
    enrich_system = """You are an expert realistic photographer and prompt engineer for Flux.
Translate the user's prompt into a clean English photography prompt.
IMPORTANT RULES:
- If user asks for a Russian / Slavic woman, describe her explicitly: 'candid 35mm photo of an authentic 23-year-old Slavic Russian woman with natural light brown or blonde hair, expressive eyes, realistic skin texture with pores and natural makeup, real human portrait'.
- If in bed in morning: 'resting peacefully in cozy morning bed with white linen, gentle window sunlight'.
- DO NOT use negative words like 'no anime, no doll' (they cause token bleed). Instead describe ONLY desired positive real-life photographic elements!
- Output ONLY 1-2 concise English sentences."""

    c = get_genai_client()
    for model in CANDIDATE_MODELS:
        try:
            resp = await c.aio.models.generate_content(
                model=model,
                contents=f"User request: '{user_prompt}'\n\nPhotographic English Prompt:",
                config={"system_instruction": enrich_system, "temperature": 0.2}
            )
            if resp and resp.text:
                cleaned = resp.text.strip().replace('"', '')
                logger.info(f"Enriched prompt via {model}: '{user_prompt}' -> '{cleaned}'")
                return cleaned
        except Exception as e:
            logger.warning(f"Model {model} failed for prompt enrichment: {e}")

    return apply_heuristic_enrichment(user_prompt)


async def refine_prompt_with_ai(old_prompt: str, user_feedback: str) -> str:
    """
    Combines previous prompt with user's feedback into an updated realistic prompt.
    """
    prompt_to_gemini = f"""Previous image prompt:
"{old_prompt}"

User feedback / complaint:
"{user_feedback}"

Generate a new detailed English photography prompt for Flux that directly fixes the issue.
Emphasize: authentic real-life Slavic Russian facial features, natural skin texture with fine pores, candid 35mm photography, natural sunlight.
Output ONLY the resulting English prompt in 1-2 sentences."""

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

    return apply_heuristic_enrichment(f"{old_prompt}, {user_feedback}")


async def generate_image_bytes(prompt: str, user_id: Optional[int] = None, is_already_en: bool = False, force_engine: Optional[str] = None) -> Tuple[bool, Optional[bytes], str, str]:
    """
    Generates image based on text prompt using Flux AI with enhance=false to avoid cartoon/anime filters.
    Returns (success, image_bytes, original_prompt, enriched_en_prompt).
    """
    clean_prompt = prompt.strip()
    clean_prompt = re.sub(r"^(?:изображение|картинка|фото|арт|рисунок):\s*", "", clean_prompt, flags=re.IGNORECASE).strip()
    
    if not clean_prompt:
        return False, None, "", "Укажите описание картинки."

    if not is_already_en:
        en_prompt = await translate_and_enrich_prompt(clean_prompt)
    else:
        en_prompt = clean_prompt

    engine = force_engine or "flux"
    if user_id:
        set_last_image_prompt(user_id, clean_prompt, en_prompt)
        set_user_awaiting_image(user_id, False)
        if not force_engine:
            engine = get_user_engine(user_id)

    encoded = urllib.parse.quote(en_prompt)
    # enhance=false prevents Pollinations from injecting anime/k-pop tokens
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model={engine}&enhance=false&seed={int(time.time()*1000)%100000}"

    logger.info(f"Generating image via {engine} (enhance=false) for: '{en_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=55)) as resp:
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
