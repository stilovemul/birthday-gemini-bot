import re
import json
import logging
from typing import Dict, Any, Optional
from core.gemini import ask_gemini

logger = logging.getLogger("PromptStudio")

AI_TARGET_MODELS = {
    "chatgpt": {
        "title": "🤖 ChatGPT / GPT-4o",
        "badge": "OpenAI",
        "description": "Структурированные системные промпты, контекст, форматирование Markdown/JSON, few-shot примеры."
    },
    "claude": {
        "title": "🧠 Claude 3.5 Sonnet",
        "badge": "Anthropic",
        "description": "Промпты с XML-тегами (<context>, <instructions>, <thinking>), глубоким анализом и длинным контекстом."
    },
    "midjourney": {
        "title": "🎨 Midjourney v6 / Niji",
        "badge": "Midjourney",
        "description": "Графические промпты на английском с параметрами (--ar 16:9, --v 6.0, --style raw, lighting, optics)."
    },
    "flux_sd": {
        "title": "🖼 Flux.1 / Stable Diffusion",
        "badge": "Black Forest Labs / Stability",
        "description": "Точные визуальные описания, веса (LoRA), негативные промпты (Negative Prompts)."
    },
    "gemini": {
        "title": "💎 Gemini 2.0 / 1.5 Pro",
        "badge": "Google DeepMind",
        "description": "Мультимодальные промпты с расчетом на многоступенчатую логику, код и структурированный вывод."
    },
    "deepseek": {
        "title": "⚡️ DeepSeek V3 / R1",
        "badge": "DeepSeek AI",
        "description": "Промпты для глубоких математических, программных и аналитических цепочек рассуждений (Chain of Thought)."
    },
    "video_ai": {
        "title": "🎬 Sora / Runway Gen-3 / Luma",
        "badge": "Video AI",
        "description": "Промпты для динамического видео: движение камеры (pan, tilt, zoom), кинематографичное освещение, FPS."
    }
}


async def generate_super_prompt(user_id: int, task: str, target_ai: str = "chatgpt") -> Dict[str, Any]:
    model_info = AI_TARGET_MODELS.get(target_ai, AI_TARGET_MODELS["chatgpt"])
    
    prompt = (
        f"Ты мировой эксперт по Prompt Engineering (составлению промптов высшего уровня для нейросетей).\n"
        f"Целевая нейросеть: {model_info['title']} ({model_info['description']})\n"
        f"Задача / сырая идея пользователя: '{task}'\n\n"
        "Сформируй идеальный, готовый к копированию промпт, максимально раскрывающий возможности этой нейросети.\n\n"
        "Требования к промпту в зависимости от типа модели:\n"
        "- Для ТЕКСТОВЫХ ИИ (ChatGPT, Claude, Gemini, DeepSeek): назначь четкую роль эксперта, задай контекст, входные данные, пошаговую инструкцию (Chain-of-Thought), ограничения, желаемый формат вывода (таблицы, списки, код, JSON).\n"
        "- Для ГРАФИЧЕСКИХ ИИ (Midjourney, Flux/SD): переведи и оформи на идеальном АНГЛИЙСКОМ языке с деталями: субъект, композиция, ракурс камеры, объектив (85mm lens, f/1.8), освещение (volumetric lighting, golden hour), стиль (photorealistic, cinematic, octane render), плюс все технические параметры (--ar 16:9 --v 6.0 --style raw --q 2) и Negative Prompt при необходимости.\n"
        "- Для ВИДЕО ИИ (Sora, Runway, Luma): укажи движение камеры (slow dolly in, cinematic drone shot, FPV), плавность движения, стиль света и атмосферу.\n\n"
        "Верни ответ СТРОГО в формате JSON:\n"
        "{\n"
        f'  "target_ai": "{model_info["title"]}",\n'
        '  "optimized_prompt": "ПОЛНЫЙ ГОТОВЫЙ ТЕКСТ ПРОМПТА ДЛЯ КОПИРОВАНИЯ",\n'
        '  "explanation": "Краткое объяснение, почему промпт составлен именно так и какие фишки использованы",\n'
        '  "recommended_settings": "Температура, параметры, аспектное соотношение или режим работы",\n'
        '  "pro_tip": "Лайфхак, как докрутить результат при общении с нейросетью"\n'
        "}"
    )

    resp = await ask_gemini(user_id, prompt)
    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing prompt studio JSON: {e}")

    return {
        "target_ai": model_info["title"],
        "optimized_prompt": f"Act as a senior expert in this domain. Execute the following task with highest quality and step-by-step reasoning: {task}",
        "explanation": "Стандартный структурированный промпт с назначением роли и пошаговым выполнением.",
        "recommended_settings": "Default temperature: 0.7",
        "pro_tip": "Уточняйте детали в следующем сообщении диалога для идеального результата."
    }
