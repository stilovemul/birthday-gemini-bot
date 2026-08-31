import io
import logging
import urllib.parse
import urllib.request
import aiohttp
import asyncio
import time
import json
import re
from typing import Optional, Tuple, Dict, Any
from core.gemini import get_genai_client, CANDIDATE_MODELS

logger = logging.getLogger("ImageGenerator")

# Active Image Studio Sessions: {user_id: {"active": True, "history": [str], "current_en_prompt": str, "last_ru_prompt": str, "updated_at": float}}
active_image_sessions: Dict[int, Dict[str, Any]] = {}

# In-memory store for user engine preference: {user_id: "realvis" | "flux" | "turbo" | "flux-anime"}
user_engines: Dict[int, str] = {}

# Active prompt awaiting mode: {user_id: True}
user_awaiting_image_prompt: Dict[int, bool] = {}


def start_image_session(user_id: int, initial_prompt: str, en_prompt: str) -> None:
    active_image_sessions[user_id] = {
        "active": True,
        "history": [initial_prompt],
        "current_en_prompt": en_prompt.strip(),
        "last_ru_prompt": initial_prompt.strip(),
        "updated_at": time.time()
    }
    user_awaiting_image_prompt[user_id] = False
    logger.info(f"Image session STARTED for user {user_id}: '{initial_prompt}'")


def update_image_session(user_id: int, new_ru_prompt: str, new_en_prompt: str) -> None:
    if user_id in active_image_sessions:
        active_image_sessions[user_id]["history"].append(new_ru_prompt)
        active_image_sessions[user_id]["current_en_prompt"] = new_en_prompt.strip()
        active_image_sessions[user_id]["last_ru_prompt"] = new_ru_prompt.strip()
        active_image_sessions[user_id]["updated_at"] = time.time()
        logger.info(f"Image session UPDATED for user {user_id}: '{new_ru_prompt}'")
    else:
        start_image_session(user_id, new_ru_prompt, new_en_prompt)


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
            "timestamp": sess["updated_at"]
        }
    return None


def apply_heuristic_enrichment(raw_prompt: str) -> str:
    """Applies high-beauty, youthful feminine portrait and athletic body tokens."""
    p_lower = raw_prompt.lower()
    tags = []

    # Hair color
    hair_token = "natural blonde hair"
    if any(k in p_lower for k in ["рыж", "рыженьк", "redhead", "ginger"]):
        hair_token = "vibrant natural ginger red hair"
    elif any(k in p_lower for k in ["брюнетк", "темн", "черн", "brunette"]):
        hair_token = "rich glossy brunette hair"
    elif any(k in p_lower for k in ["блондинк", "светл", "blonde"]):
        hair_token = "platinum blonde hair with soft waves"

    # Framing / Body
    framing = "candid raw 35mm photograph"
    if any(k in p_lower for k in ["пресс", "живот", "кубик", "фигур", "тел", "abs", "stomach"]):
        framing = "medium shot showing her fit toned athletic torso, visible defined six-pack abs on flat stomach"

    if any(k in p_lower for k in ["девушк", "женщин", "красавиц", "модель", "girl", "woman"]):
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
- Ensure the female face is STUNNINGLY GORGEOUS, young (21-23yo), highly feminine, attractive, with soft delicate facial features and a warm lovely smile (avoid harsh, tired, or masculine jawline).
- If user requests abs/stomach/body (e.g. 'пресс на живот', 'кубики', 'фигура'): make sure the camera framing is a 'medium shot showing her toned flat stomach and defined fit abs'.
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
    Combines previous prompt with user's feedback into an updated realistic prompt.
    """
    prompt_to_gemini = f"""Previous image prompt:
"{old_prompt}"

User modification:
"{user_feedback}"

Generate an updated, detailed English photography prompt for RealVisXL that merges the user's modification.
CRITICAL INSTRUCTIONS:
- If user asks for abs/stomach/body ('пресс на живот', 'кубики', 'фигура'): adjust framing to 'medium shot or seated in bed, clearly showing her fit athletic flat stomach with defined six-pack abs and toned torso'. Do NOT do a tight headshot!
- ALWAYS enforce: stunningly beautiful, young (22yo), charming and feminine face with delicate features, radiant skin, and attractive smile (never tired or masculine).
- Preserve previous features (e.g. hair color, morning bed) unless the user explicitly asks to change them!
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


async def generate_via_realvis_horde(prompt: str) -> Optional[bytes]:
    """Generates 100% photorealistic human photo via RealVisXL V4.0 / Juggernaut XL with beauty filters."""
    # Explicit negative prompt to eliminate masculine jaw, tired eyes, wrinkled skin, or wrong cropping
    negative_prompt = (
        "anime, 3d, doll, drawing, painting, cartoon, asian, smooth plastic, artificial, airbrush, render, "
        "harsh masculine face, masculine jawline, aged, tired eyes, dark circles under eyes, wrinkles, "
        "close-up head crop when stomach/body requested, bad anatomy, deformed body, unnatural abs"
    )
    full_prompt = f"{prompt} ### {negative_prompt}"
    payload = {
        "prompt": full_prompt,
        "params": {
            "sampler_name": "k_dpmpp_2m",
            "cfg_scale": 7,
            "steps": 25,
            "width": 1024,
            "height": 1024,
            "n": 1
        },
        "models": ["RealVisXL V4.0", "Juggernaut XL", "ICBINP - I Can't Believe It's Not Photography", "SDXL 1.0"]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://stablehorde.net/api/v2/generate/async",
                json=payload,
                headers={"Content-Type": "application/json", "apikey": "0000000000", "Client-Agent": "AiGemBot:1.0"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 202:
                    return None
                data = await resp.json()
                task_id = data.get("id")
                if not task_id:
                    return None

            for _ in range(7):
                await asyncio.sleep(3)
                async with session.get(
                    f"https://stablehorde.net/api/v2/generate/check/{task_id}",
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as c_resp:
                    c_data = await c_resp.json()
                    if c_data.get("done"):
                        async with session.get(
                            f"https://stablehorde.net/api/v2/generate/status/{task_id}",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as r_resp:
                            r_data = await r_resp.json()
                            generations = r_data.get("generations", [])
                            if generations and generations[0].get("img"):
                                img_url = generations[0]["img"]
                                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=15)) as img_resp:
                                    if img_resp.status == 200:
                                        img_bytes = await img_resp.read()
                                        logger.info(f"RealVisXL successfully generated photo ({len(img_bytes)} bytes)")
                                        return img_bytes
                        break
    except Exception as e:
        logger.warning(f"RealVisXL generation error/timeout: {e}")
    return None


async def generate_image_bytes(prompt: str, user_id: Optional[int] = None, is_already_en: bool = False, force_engine: Optional[str] = None) -> Tuple[bool, Optional[bytes], str, str]:
    """
    Generates image based on text prompt with RealVisXL high-fidelity photorealism.
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

    engine = force_engine or "realvis"
    if user_id:
        user_awaiting_image_prompt[user_id] = False
        if not force_engine:
            engine = get_user_engine(user_id)

    # 1. Try RealVisXL Photorealism first
    if engine == "realvis" or "real" in engine:
        img_bytes = await generate_via_realvis_horde(en_prompt)
        if img_bytes and len(img_bytes) > 5000:
            return True, img_bytes, clean_prompt, en_prompt

    # 2. Fast Fallback via Clean Flux with enhance=false
    encoded = urllib.parse.quote(en_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux&enhance=false&seed={int(time.time()*1000)%100000}"

    logger.info(f"Generating image via Flux (enhance=false) for: '{en_prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=45)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 5000:
                        return True, data, clean_prompt, en_prompt
                    else:
                        return False, None, clean_prompt, "Сгенерированное изображение повреждено."
                else:
                    return False, None, clean_prompt, f"Ошибка генерации: HTTP {resp.status}"
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return False, None, clean_prompt, f"Ошибка генерации: {e}"
