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

# In-memory store for user engine preference: {user_id: "flux-realism" | "turbo" | "flux-anime" | "flux-3d"}
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
    return user_engines.get(user_id, "flux-realism")


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
    """Applies high-grade camera tags to eliminate doll/3D looks and force authentic raw photography."""
    p_lower = raw_prompt.lower()
    tags = []

    # Photography & anti-doll realism tokens
    camera_tags = (
        "authentic candid raw photograph, shot on Sony A7 IV 85mm f/1.8 lens, "
        "natural realistic skin texture with visible pores and natural imperfections, "
        "detailed realistic eyes and fine hair strands, authentic natural lighting, "
        "no 3D render, no anime, no plastic doll skin, no airbrushing, no digital painting, "
        "unedited real-life photo, high resolution 8k"
    )

    if any(k in p_lower for k in ["девушк", "женщин", "красавиц", "модель", "girl", "woman"]):
        if any(r in p_lower for r in ["русск", "росси", "славян"]):
            tags.append(f"close-up candid raw photograph of a 22-year-old beautiful natural Russian woman, {camera_tags}")
        else:
            tags.append(f"candid raw portrait of a beautiful natural woman, {camera_tags}")
    elif any(k in p_lower for k in ["парен", "мужчин", "человек", "man", "guy"]):
        tags.append(f"candid raw portrait of a man, {camera_tags}")
    elif any(k in p_lower for k in ["кот", "кошк", "котен", "котик", "cat"]):
        tags.append("adorable realistic cat, highly detailed fluffy fur, clear eyes, natural daylight, candid pet photography")
    elif any(k in p_lower for k in ["машин", "авто", "спорткар", "автомобил", "car"]):
        tags.append("real-life automotive photography of a sports car, glossy reflections, natural ambient daylight, 8k raw photo")

    if tags:
        return f"{raw_prompt}, {', '.join(tags)}"
    return f"{raw_prompt}, {camera_tags}"


async def translate_and_enrich_prompt(user_prompt: str) -> str:
    """
    Translates Russian prompt into rich, realistic English prompt optimized for Flux-Realism.
    """
    enrich_system = """You are an expert AI photographer and prompt engineer for photorealistic diffusion models (Flux Realism).
Translate the user's image request from Russian into an authentic, raw, unedited English photograph prompt.
CRITICAL RULES TO AVOID DOLL/ANIME LOOK:
- Ensure the subject looks like a 100% REAL human being, NOT an anime character, NOT a plastic doll, NOT a smooth 3D render.
- Add camera specs: 'candid authentic photograph, shot on Sony A7 IV 85mm f/1.8 lens, natural daylight, real human skin texture with pores, realistic eyes and natural messy hair, unedited real life photo, 8k'.
- If the setting is 'в постели утром' (in bed morning), describe: 'cozy morning bed sheets, soft morning daylight filtering through bedroom window, relaxed natural pose'.
- Output ONLY the final English prompt in 1-2 sentences."""

    c = get_genai_client()
    for model in CANDIDATE_MODELS:
        try:
            resp = await c.aio.models.generate_content(
                model=model,
                contents=f"User request: '{user_prompt}'\n\nPhotorealistic English Camera Prompt:",
                config={"system_instruction": enrich_system, "temperature": 0.2}
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
    Combines previous prompt with user's feedback into an updated realistic prompt.
    """
    prompt_to_gemini = f"""Previous image prompt:
"{old_prompt}"

User feedback / complaint:
"{user_feedback}"

Generate a new detailed English diffusion prompt for Flux-Realism that directly addresses the user's feedback.
If user says 'нереалистично' (unrealistic), 'кукла' (doll-like), or 'пластик' (plastic):
- Strongly enforce: 'raw authentic 35mm candid photo, real human face, detailed skin pores, realistic imperfect texture, soft morning natural lighting, no plastic doll skin, no 3d render, no anime'.
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


async def generate_image_bytes(prompt: str, user_id: Optional[int] = None, is_already_en: bool = False, force_engine: Optional[str] = None) -> Tuple[bool, Optional[bytes], str, str]:
    """
    Generates image based on text prompt using high-speed Flux-Realism / Turbo AI model.
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

    engine = force_engine or "flux-realism"
    if user_id:
        set_last_image_prompt(user_id, clean_prompt, en_prompt)
        set_user_awaiting_image(user_id, False)
        if not force_engine:
            engine = get_user_engine(user_id)

    encoded = urllib.parse.quote(en_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model={engine}&seed={int(time.time()*1000)%100000}"

    logger.info(f"Generating image via {engine} for: '{en_prompt}'")
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
