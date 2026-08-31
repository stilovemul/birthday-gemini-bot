import io
import logging
import urllib.parse
import urllib.request
import aiohttp
import asyncio
import time
import json
import re
import random
from typing import Optional, Tuple, Dict, Any
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("ImageGenerator")

# Active Image Studio Sessions:
# {user_id: {"active": True, "seed": int, "history": [str], "current_en_prompt": str, "last_ru_prompt": str, "updated_at": float}}
active_image_sessions: Dict[int, Dict[str, Any]] = {}

# In-memory store for user engine preference: {user_id: "realvis" | "flux" | "turbo" | "flux-anime"}
user_engines: Dict[int, str] = {}

# Active prompt awaiting mode: {user_id: True}
user_awaiting_image_prompt: Dict[int, bool] = {}


def start_image_session(user_id: int, initial_prompt: str, en_prompt: str, seed: Optional[int] = None) -> int:
    if seed is None:
        seed = random.randint(100000, 2147483640)
    
    active_image_sessions[user_id] = {
        "active": True,
        "seed": seed,
        "history": [initial_prompt],
        "current_en_prompt": en_prompt.strip(),
        "last_ru_prompt": initial_prompt.strip(),
        "updated_at": time.time()
    }
    user_awaiting_image_prompt[user_id] = False
    logger.info(f"Image session STARTED for user {user_id} with locked seed {seed}: '{initial_prompt}'")
    return seed


def update_image_session(user_id: int, new_ru_prompt: str, new_en_prompt: str) -> int:
    if user_id in active_image_sessions:
        sess = active_image_sessions[user_id]
        sess["history"].append(new_ru_prompt)
        sess["current_en_prompt"] = new_en_prompt.strip()
        sess["last_ru_prompt"] = new_ru_prompt.strip()
        sess["updated_at"] = time.time()
        logger.info(f"Image session UPDATED for user {user_id} (preserving seed {sess['seed']}): '{new_ru_prompt}'")
        return sess["seed"]
    else:
        return start_image_session(user_id, new_ru_prompt, new_en_prompt)


def reset_session_seed(user_id: int) -> int:
    new_seed = random.randint(100000, 2147483640)
    if user_id in active_image_sessions:
        active_image_sessions[user_id]["seed"] = new_seed
        logger.info(f"New seed generated for user {user_id}: {new_seed}")
    return new_seed


def end_image_session(user_id: int) -> bool:
    if user_id in active_image_sessions:
        del active_image_sessions[user_id]
        logger.info(f"Image session ENDED for user {user_id}")
        return True
    return False


def is_in_image_session(user_id: int) -> bool:
    sess = active_image_sessions.get(user_id)
    if sess and sess.get("active"):
        return True
    return False


def get_image_session(user_id: int) -> Optional[Dict[str, Any]]:
    return active_image_sessions.get(user_id)


def set_user_awaiting_image(user_id: int, status: bool = True) -> None:
    user_awaiting_image_prompt[user_id] = status


def is_user_awaiting_image(user_id: int) -> bool:
    return user_awaiting_image_prompt.get(user_id, False)


def set_user_engine(user_id: int, engine: str) -> None:
    user_engines[user_id] = engine


def get_user_engine(user_id: int) -> str:
    return user_engines.get(user_id, "realvis")


def get_last_image_info(user_id: int) -> Optional[Dict[str, Any]]:
    sess = active_image_sessions.get(user_id)
    if sess:
        return {
            "prompt": sess["last_ru_prompt"],
            "en_prompt": sess["current_en_prompt"],
            "seed": sess["seed"],
            "timestamp": sess["updated_at"]
        }
    return None


def apply_heuristic_enrichment(raw_prompt: str) -> str:
    """Applies pure raw 35mm analog photography tokens with correct human anatomy."""
    p_lower = raw_prompt.lower()
    tags = []

    hair_token = "natural blonde hair with soft strands"
    if any(k in p_lower for k in ["рыж", "рыженьк", "redhead", "ginger"]):
        hair_token = "vibrant natural ginger red hair with subtle freckles"
    elif any(k in p_lower for k in ["брюнетк", "темн", "черн", "brunette"]):
        hair_token = "rich dark brunette hair"
    elif any(k in p_lower for k in ["блондинк", "светл", "blonde", "пепельн"]):
        hair_token = "natural platinum blonde hair with soft waves"

    framing = "candid raw 35mm analog photograph, naturally seated, perfect human anatomy, realistic body proportions"
    if any(k in p_lower for k in ["пресс", "живот", "кубик", "фигур", "тел", "abs", "stomach"]):
        framing = "candid medium portrait naturally seated, fit toned flat stomach with visible subtle abs, correct natural anatomy"

    if any(k in p_lower for k in ["девушк", "женщин", "красавиц", "модель", "girl", "woman", "обнажен"]):
        tags.append(f"{framing} of an authentic 22-year-old gorgeous Slavic Russian woman, natural feminine face, {hair_token}, realistic human skin texture with pores, soft natural daylight, genuine unposed photo")
    elif any(k in p_lower for k in ["парен", "мужчин", "человек", "man", "guy"]):
        tags.append("candid portrait photograph of an attractive young man, authentic human facial features, natural lighting, real photography")

    if any(k in p_lower for k in ["постел", "кроват", "утром", "утро", "bed", "morning"]):
        tags.append("relaxing naturally on bed sheets, soft morning natural sunlight from bedroom window, authentic lifestyle photo")
    elif any(k in p_lower for k in ["машин", "авто", "салон", "car"]):
        tags.append("inside car cabin, natural daylight through car window, authentic candid shot")

    if tags:
        return f"{', '.join(tags)}"
    return f"{raw_prompt}, candid 35mm photography, natural lighting, authentic real life photo, correct human anatomy"


async def translate_and_enrich_prompt(user_prompt: str) -> str:
    """
    Translates Russian prompt into clean, raw 35mm analog photography prompt with correct anatomy.
    """
    enrich_system = """You are a master analog photographer and prompt engineer for RealVisXL V4.0.
Convert the user's prompt into an authentic raw 35mm photographic description.
CRITICAL RULES:
- Ensure CORRECT NATURAL HUMAN ANATOMY: Avoid extreme distorted poses, pretzel legs, or twisted spines. Prefer natural seated, standing or reclining poses with realistic proportions.
- If a Russian/Slavic woman is requested: 'candid raw 35mm analog photo of an authentic 22-year-old gorgeous Slavic Russian woman, natural facial features, real skin pores, realistic feminine anatomy, natural lighting'.
- NEVER allow anime, 3D, CGI, doll-like or airbrushed plastic aesthetics.
- Return ONLY 1-2 concise English sentences."""

    c = get_genai_client()
    for model in CANDIDATE_MODELS:
        try:
            resp = await c.aio.models.generate_content(
                model=model,
                contents=f"User prompt: '{user_prompt}'\n\nAnalog Photo Prompt:",
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
    Carefully updates ONLY the requested delta changes while strictly preserving natural anatomy and realism.
    """
    prompt_to_gemini = f"""You are an expert realistic photo inpainting engineer for RealVisXL.
BASE PHOTO DESCRIPTION:
"{old_prompt}"

USER MODIFICATION:
"{user_feedback}"

TASK:
Produce an updated raw 35mm photographic prompt merging ONLY the requested change into the base photo.
Ensure: perfect natural human anatomy, realistic body proportions, authentic Slavic Russian facial features, real skin pores, raw unedited 35mm camera look.
Output ONLY the resulting 1-2 sentence English prompt."""

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


async def generate_via_realvis_horde(prompt: str, seed: Optional[int] = None) -> Optional[bytes]:
    """Generates 100% authentic raw human photo via RealVisXL V4.0 / Juggernaut XL with anti-mutation negatives."""
    # Comprehensive negative prompt eliminating anatomical mutations, extra limbs, broken spines, and 3D/anime
    negative_prompt = (
        "deformed limbs, extra legs, mutated legs, bad anatomy, broken spine, malformed torso, "
        "extra limbs, disconnected limbs, missing limbs, bad proportions, unnatural body twisting, "
        "mutated body, anatomically incorrect, mutilated, disfigured, hollow stomach, "
        "anime, 3d, doll, cgi, render, drawing, painting, cartoon, asian, smooth plastic, artificial, "
        "airbrush, digital art, photoshop, airbrushed skin, plastic face, fake eyes, harsh masculine face"
    )
    full_prompt = f"{prompt} ### {negative_prompt}"
    
    params: Dict[str, Any] = {
        "sampler_name": "k_dpmpp_2m",
        "cfg_scale": 5.5,  # 5.5 prevents over-saturation and body distortion
        "steps": 28,
        "width": 1024,
        "height": 1024,
        "n": 1
    }
    if seed is not None:
        params["seed"] = str(seed)

    payload = {
        "prompt": full_prompt,
        "params": params,
        "models": ["RealVisXL V4.0", "Juggernaut XL", "ICBINP - I Can't Believe It's Not Photography"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://stablehorde.net/api/v2/generate/async",
                json=payload,
                headers={"Content-Type": "application/json", "apikey": "0000000000", "Client-Agent": "AiGemBot:1.0"},
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:
                if resp.status != 202:
                    return None
                data = await resp.json()
                task_id = data.get("id")
                if not task_id:
                    return None

            for _ in range(6):
                await asyncio.sleep(2.5)
                async with session.get(
                    f"https://stablehorde.net/api/v2/generate/check/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=6)
                ) as c_resp:
                    c_data = await c_resp.json()
                    if c_data.get("done"):
                        async with session.get(
                            f"https://stablehorde.net/api/v2/generate/status/{task_id}",
                            timeout=aiohttp.ClientTimeout(total=8)
                        ) as r_resp:
                            r_data = await r_resp.json()
                            generations = r_data.get("generations", [])
                            if generations and generations[0].get("img"):
                                img_url = generations[0]["img"]
                                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=15)) as img_resp:
                                    if img_resp.status == 200:
                                        img_bytes = await img_resp.read()
                                        logger.info(f"RealVisXL (seed {seed}) generated true authentic photo ({len(img_bytes)} bytes)")
                                        return img_bytes
                        break
    except Exception as e:
        logger.warning(f"RealVisXL generation timeout/error: {e}")
    return None


async def generate_image_bytes(
    prompt: str,
    user_id: Optional[int] = None,
    is_already_en: bool = False,
    force_engine: Optional[str] = None,
    seed: Optional[int] = None
) -> Tuple[bool, Optional[bytes], str, str, int]:
    """
    Generates image with RealVisXL high photorealism priority and natural anatomy.
    Returns (success, image_bytes, original_prompt, enriched_en_prompt, seed_used).
    """
    clean_prompt = prompt.strip()
    clean_prompt = re.sub(r"^(?:изображение|картинка|фото|арт|рисунок):\s*", "", clean_prompt, flags=re.IGNORECASE).strip()
    
    if not clean_prompt:
        return False, None, "", "Укажите описание картинки.", 0

    if not is_already_en:
        en_prompt = await translate_and_enrich_prompt(clean_prompt)
    else:
        en_prompt = clean_prompt

    engine = force_engine or "realvis"
    current_seed = seed
    if user_id:
        user_awaiting_image_prompt[user_id] = False
        if not force_engine:
            engine = get_user_engine(user_id)
        if current_seed is None:
            sess = get_image_session(user_id)
            if sess:
                current_seed = sess["seed"]
            else:
                current_seed = random.randint(100000, 2147483640)

    if current_seed is None:
        current_seed = random.randint(100000, 2147483640)

    # 1. RealVisXL / Juggernaut XL Priority (True 35mm Camera Photorealism)
    if engine == "realvis" or "real" in engine:
        img_bytes = await generate_via_realvis_horde(en_prompt, seed=current_seed)
        if img_bytes and len(img_bytes) > 5000:
            return True, img_bytes, clean_prompt, en_prompt, current_seed

    # 2. Photorealistic Fallback with explicit raw photography and anatomy tokens
    photo_prompt = f"{en_prompt}, candid raw 35mm film photograph, perfect human anatomy, realistic body proportions, real skin with pores, authentic Slavic Russian facial features, natural lighting, shot on 35mm lens, NO anime, NO 3d render, NO mutated limbs, NO plastic"
    encoded = urllib.parse.quote(photo_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux&enhance=false&seed={current_seed}"

    logger.info(f"Generating image via fallback (seed {current_seed}) for: '{photo_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 5000:
                        return True, data, clean_prompt, en_prompt, current_seed
                    else:
                        return False, None, clean_prompt, "Сгенерированное изображение повреждено.", current_seed
                else:
                    return False, None, clean_prompt, f"Ошибка генерации: HTTP {resp.status}", current_seed
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return False, None, clean_prompt, f"Ошибка генерации: {e}", current_seed
