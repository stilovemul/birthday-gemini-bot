import re
import json
import logging
from typing import Dict, Any, Optional, List
from core.gemini import ask_gemini

logger = logging.getLogger("SteakMaster")


async def get_steak_guide(
    user_id: int,
    cut: str = "Рибай",
    doneness: str = "Medium Rare",
    thickness_cm: float = 2.5,
    image_bytes: Optional[bytes] = None,
    seen_titles: Optional[List[str]] = None
) -> Dict[str, Any]:
    anti_repeat = ""
    if seen_titles:
        anti_repeat = f"\nВАЖНО: Пользователь уже смотрел: {', '.join(seen_titles[-10:])}. Предложи другой интересный отруб или нюанс прожарки!"

    prompt = (
        "Ты бренд-шеф мясного стейкхауса. Рассчитай идеальный тайминг и технологию приготовления стейка.\n"
        f"Отруб: {cut}. Желаемая прожарка: {doneness}. Толщина куска: {thickness_cm} см.{anti_repeat}\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "steak_title": "🥩 Идеальный стейк Рибай (Medium Rare)",\n'
        '  "target_core_temp": "54-56°C внутри мяса",\n'
        '  "crust_sear_time": "По 2 минуты с каждой стороны на раскаленной чугунной сковороде / гриле",\n'
        '  "basting_time": "1-1.5 минуты поливать растопленным сливочным маслом с чесноком, розмарином и тимьяном",\n'
        '  "rest_time": "5 минут на теплой тарелке или деревянной доске под фольгой",\n'
        '  "total_pan_time": "5.5 минут",\n'
        '  "steps": [\n'
        '    "1. Достаньте стейк из холодильника за 30-40 мин до жарки, промокните бумажным полотенцем досуха.",\n'
        '    "2. Щедро посолите крупной морской солью и смажьте растительным маслом высокой точки дымления.",\n'
        '    "3. Выложите на сильно раскаленную сковороду. Жарьте 2 мин, переверните, жарьте еще 1.5 мин.",\n'
        '    "4. Убавьте огонь, добавьте 30г сливочного масла, 2 раздавленных зубчика чеснока и веточку розмарина. Поливайте стейк ложкой (basting) 1 минуту.",\n'
        '    "5. Снимите стейк, поперчите свежемолотым перцем и дайте отдохнуть 5 минут, чтобы соки равномерно распределились."\n'
        '  ],\n'
        '  "chef_rule": "🔥 Никогда не перчите стейк до жарки (перец сгорит на раскаленной сковороде и даст горечь) и обязательно дайте мясу отдохнуть!"\n'
        "}"
    )

    if image_bytes:
        prompt_vision = (
            "Определи отруб мяса, мраморность и толщину по этому фото. "
            "Рассчитай идеальный тайминг жарки и прожарки в формате JSON со следующими полями: "
            "steak_title, target_core_temp, crust_sear_time, basting_time, rest_time, total_pan_time, steps, chef_rule."
        )
        resp = await ask_gemini(user_id, prompt_vision, image_bytes=image_bytes)
    else:
        resp = await ask_gemini(user_id, prompt)

    try:
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.error(f"Error parsing steak master JSON: {e}")

    return {
        "steak_title": f"🥩 Стейк {cut} ({doneness})",
        "target_core_temp": "54-56°C",
        "crust_sear_time": "2 мин с каждой стороны",
        "basting_time": "1 мин со сливочным маслом и розмарином",
        "rest_time": "5 минут отдыха под фольгой",
        "total_pan_time": "5-6 минут",
        "steps": [
            "1. Обсушить мясо и согреть до комнатной температуры.",
            "2. Раскалить сковороду, посолить стейк и обжарить по 2 мин с каждой стороны.",
            "3. Добавить сливочное масло, чеснок, розмарин и поливать ложкой 1 мин.",
            "4. Дать отдохнуть 5 минут перед нарезкой."
        ],
        "chef_rule": "Дайте стейку отдохнуть ровно столько, сколько он жарился!"
    }
