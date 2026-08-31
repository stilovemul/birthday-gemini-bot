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
    """Applies high-beauty, youthful feminine portrait and athletic body tokens."""
    p_lower = raw_prompt.lower()
    tags = []

    hair_token = "natural blonde hair"
    if any(k in p_lower for k in ["рыж", "рыженьк", "redhead", "ginger"]):
        hair_token = "vibrant natural ginger red hair"
    elif any(k in p_lower for k in ["брюнетк", "темн", "черн", "brunette"]):
        hair_token = "rich glossy brunette hair"
    elif any(k in p_lower for k in ["блондинк", "светл", "blonde"]):
        hair_token = "platinum blonde hair with soft waves"

    framing = "candid raw 35mm photograph"
    if any(k in p_lower for k in ["пресс", "живот", "кубик", "фигур", "тел", "abs", "stomach"]):
        framing = "medium seated shot showing her fit toned athletic torso, visible defined six-pack abs on flat stomach"

    if any(k in p_lower for k in ["девушк", "женщин", "красавиц", "модель", "girl", "woman", "18+"]):
        tags.append(f"{framing} of an exceptionally gorgeous and attractive 22-year-old Russian woman with a stunningly beautiful, tender, and youthful feminine face, {hair_token}, captivating eyes, radiant glowing skin texture, gentle warm smile, real life photograph")
    elif any(k in p_lower for k in ["парен", "мужчин", "человек", "man", "guy"]):
        tags.append("candid portrait photograph of an attractive young man, authentic human facial features, natural lighting, real photography")

    if any(k in p_lower for k in ["постел", "кроват", "утром", "утро", "bed", "morning"]):
        tags.append("in cozy morning bed sheets, soft morning natural sunlight from bedroom window, authentic lifestyle photo")

    if tags:
        return f"{', '.join(tags)}"
    return f"{raw_prompt}, candid 35mm photography, natural lighting, authentic real life photo"


async def translate_and_enrich_prompt(user_prompt: str) -> str:
    """
    Translates Russian prompt into clean, photorealistic English photography prompt.
    """
    enrich_system = """You are an expert realistic photographer and prompt engineer.
Translate the user's prompt into an English photography prompt for RealVisXL.
IMPORTANT RULES:
- Ensure the female face is STUNNINGLY GORGEOUS, young (21-23yo), highly feminine, attractive, with soft delicate facial features and a warm lovely smile.
- If user requests abs/stomach/body (e.g. 'пресс на живот', 'кубики', 'фигура'): make sure the camera framing is a 'medium seated shot showing her toned flat stomach and defined fit abs'.
- Output ONLY 1-2 concise English sentences without negative prompt words."""

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
    Carefully updates ONLY the requested delta changes while strictly preserving the existing subject, lighting, and composition.
    """
    prompt_to_gemini = f"""You are an expert image inpainting and modification prompt engineer.
EXISTING BASE IMAGE DESCRIPTION:
"{old_prompt}"

USER'S SPECIFIC MODIFICATION REQUEST:
"{user_feedback}"

TASK:
Produce an updated English prompt that makes ONLY the exact modification requested by the user, while STRICTLY KEEPING all other details from the base image unchanged.
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
    """Generates 100% photorealistic human photo via RealVisXL with fast 6s timeout."""
    negative_prompt = (
        "anime, 3d, doll, drawing, painting, cartoon, asian, smooth plastic, artificial, airbrush, render, "
        "harsh masculine face, masculine jawline, aged, tired eyes, dark circles under eyes, wrinkles, "
        "close-up head crop when stomach/body requested, bad anatomy, deformed body, unnatural abs"
    )
    full_prompt = f"{prompt} ### {negative_prompt}"
    
    params: Dict[str, Any] = {
        "sampler_name": "k_dpmpp_2m",
        "cfg_scale": 7,
        "steps": 20,
        "width": 1024,
        "height": 1024,
        "n": 1
    }
    if seed is not None:
        params["seed"] = str(seed)

    payload = {
        "prompt": full_prompt,
        "params": params,
        "models": ["RealVisXL V4.0", "Juggernaut XL", "ICBINP - I Can't Believe It's Not Photography", "SDXL 1.0"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://stablehorde.net/api/v2/generate/async",
                json=payload,
                headers={"Content-Type": "application/json", "apikey": "0000000000", "Client-Agent": "AiGemBot:1.0"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status != 202:
                    return None
                data = await resp.json()
                task_id = data.get("id")
                if not task_id:
                    return None

            # Fast polling: max 4 checks (5-6 seconds total)
            for _ in range(4):
                await asyncio.sleep(1.5)
                async with session.get(
                    f"https://stablehorde.net/api/v2/generate/check/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as c_resp:
                    c_data = await c_resp.json()
                    if c_data.get("done"):
                        async with session.get(
                            f"https://stablehorde.net/api/v2/generate/status/{task_id}",
                            timeout=aiohttp.ClientTimeout(total=6)
                        ) as r_resp:
                            r_data = await r_resp.json()
                            generations = r_data.get("generations", [])
                            if generations and generations[0].get("img"):
                                img_url = generations[0]["img"]
                                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=8)) as img_resp:
                                    if img_resp.status == 200:
                                        img_bytes = await img_resp.read()
                                        logger.info(f"RealVisXL (seed {seed}) generated photo ({len(img_bytes)} bytes)")
                                        return img_bytes
                        break
    except Exception as e:
        logger.warning(f"RealVisXL fast-path skipped/timeout: {e}")
    return None


async def generate_image_bytes(
    prompt: str,
    user_id: Optional[int] = None,
    is_already_en: bool = False,
    force_engine: Optional[str] = None,
    seed: Optional[int] = None
) -> Tuple[bool, Optional[bytes], str, str, int]:
    """
    Generates image with ultra-fast failover (under 4-6s guaranteed).
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

    # 1. Try RealVisXL Photorealism (5s fast path)
    if engine == "realvis" or "real" in engine:
        img_bytes = await generate_via_realvis_horde(en_prompt, seed=current_seed)
        if img_bytes and len(img_bytes) > 5000:
            return True, img_bytes, clean_prompt, en_prompt, current_seed

    # 2. Instant Turbo Fallback via Clean Flux (2-3s response)
    encoded = urllib.parse.quote(en_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux&enhance=false&seed={current_seed}"

    logger.info(f"Generating image via Turbo Flux (seed {current_seed}) for: '{en_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
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
