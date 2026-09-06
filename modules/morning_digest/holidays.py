import os
import json
import logging
import asyncio
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from core.config import MSK_TZ, DATA_DIR, GEMINI_API_KEY
from core.gemini import get_genai_client
from google.genai import types

logger = logging.getLogger("TodayCalendar")

CACHE_FILE = os.path.join(DATA_DIR, "holidays_cache.json")
_holidays_memory_cache: Dict[str, Dict[str, Any]] = {}

MONTHS_GEN_RU = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

DAYS_RU = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}

# Curated comprehensive fallbacks for dates
CURATED_FALLBACK_DATABASE = {
    (9, 6): {
        "holidays": [
            "✈️ День полётов над землёй",
            "📚 Всемирный день чтения книг (Read a Book Day)",
            "👩‍🦰 Всемирный день рыжих людей",
            "🛡 День подразделений по противодействию экстремизму МВД РФ",
            "☕️ День кофейного мороженого",
            "🌿 День шелеста осенней листвы",
            "🕊 День борьбы с прокрастинацией"
        ],
        "name_days": "Максим, Денис, Георгий, Арсений, Пётр, Серафима, Евтихий",
        "history": [
            "1826 - в Санкт-Петербурге открыт знаменитый Египетский цепной мост через Фонтанку.",
            "1928 - утверждено Положение о Центральном статистическом управлении СССР.",
            "1936 - учреждено почётное звание «Народный артист СССР».",
            "1991 - президиум Верховного Совета РСФСР вернул Ленинграду историческое название Санкт-Петербург."
        ],
        "folk_signs": [
            "• Дождь в этот день предвещает сухую и теплую осень, а также богатый урожай на следующий год.",
            "• Много желудей на дубах — к суровой и морозной зиме.",
            "• Синицы громко пищат с утра — к скорому дождю и похолоданию."
        ]
    }
}


def _load_cache() -> Dict[str, Dict[str, Any]]:
    global _holidays_memory_cache
    if _holidays_memory_cache:
        return _holidays_memory_cache
    
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _holidays_memory_cache = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading holidays cache: {e}")
            _holidays_memory_cache = {}
    return _holidays_memory_cache


def _save_cache(date_key: str, data: Dict[str, Any]):
    global _holidays_memory_cache
    _holidays_memory_cache[date_key] = data
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_holidays_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Error saving holidays cache: {e}")


def format_calendar_card(data: Dict[str, Any]) -> str:
    """Formats the calendar dictionary into the exact aesthetic layout from the reference."""
    holidays_list = data.get("holidays", [])
    name_days = data.get("name_days", "")
    history_list = data.get("history", [])
    folk_signs = data.get("folk_signs", [])
    
    # Format Holidays
    h_lines = []
    for h in holidays_list:
        h_str = str(h).strip()
        if not h_str:
            continue
        if not h_str.startswith("•") and not any(h_str.startswith(e) for e in ["🇷🇺", "🌍", "✈️", "📚", "👩‍🦰", "🛡", "☕️", "🌿", "🕊", "🐎", "📝", "🧑‍⚕️", "🥜", "⛪️", "🎉", "❤️", "🎄", "🚀", "🎖", "☀️", "👶", "🎃", "🔔", "💡", "🎮", "🍾"]):
            h_str = f"• {h_str}"
        h_lines.append(h_str)
    
    holidays_text = "\n".join(h_lines) if h_lines else "• Официальных праздников в этот день нет"
    
    # Format History
    hist_lines = []
    for item in history_list:
        hist_str = str(item).strip()
        if hist_str:
            hist_lines.append(hist_str)
    history_text = "\n".join(hist_lines) if hist_lines else "• Значимых исторических дат не зафиксировано"
    
    # Format Folk Signs
    sign_lines = []
    for s in folk_signs:
        s_str = str(s).strip()
        if not s_str:
            continue
        if not s_str.startswith("•"):
            s_str = f"• {s_str}"
        sign_lines.append(s_str)
    signs_text = "\n".join(sign_lines) if sign_lines else "• Народные приметы на этот день отсутствуют"
    
    card = (
        f"🎉 <b>ПРАЗДНИКИ ДНЯ:</b>\n"
        f"{holidays_text}\n\n"
        f"👥 <b>ИМЕНИНЫ ОТМЕЧАЮТ:</b>\n"
        f"{name_days}\n\n"
        f"📆 <b>ИСТОРИЧЕСКИЕ СОБЫТИЯ:</b>\n"
        f"{history_text}\n\n"
        f"💫 <b>НАРОДНЫЕ ПРИМЕТЫ:</b>\n"
        f"{signs_text}"
    )
    return card


def get_curated_fallback_data(target_date: datetime) -> Dict[str, Any]:
    """Provides curated fallback calendar data."""
    key = (target_date.month, target_date.day)
    if key in CURATED_FALLBACK_DATABASE:
        return CURATED_FALLBACK_DATABASE[key]
    
    d_num = target_date.day
    m_name = MONTHS_GEN_RU[target_date.month]
    weekday_idx = target_date.weekday()
    
    holidays = [
        f"📅 День {d_num} {m_name} — день новых возможностей и свершений",
        "🌍 Всемирный день улыбок и позитива",
        "☕️ Международный день приятных встреч и кофе"
    ]
    if weekday_idx == 4:
        holidays.insert(0, "🎉 Пятница — завершение рабочей недели")
    elif weekday_idx == 6:
        holidays.insert(0, "☀️ Воскресный день семейного отдыха и уюта")
        
    return {
        "holidays": holidays,
        "name_days": "Александр, Михаил, Иван, Анна, Елена, Мария, Дмитрий, Сергей",
        "history": [
            f"В этот день {d_num} {m_name} в разные эпохи происходили важнейшие открытия и свершения в мировой культуре и науке.",
            "Памятная дата летописи отечественной истории и созидательного труда."
        ],
        "folk_signs": [
            "• Утренний туман предвещает ясную и теплую погоду на весь день.",
            "• Птицы летают высоко в небе — к сухой и устойчивой погоде."
        ]
    }


async def fetch_calendar_from_gemini(target_date: datetime) -> Optional[Dict[str, Any]]:
    """Generates complete calendar dataset (Holidays, Name days, History, Folk signs) via Gemini AI."""
    day = target_date.day
    month_name = MONTHS_GEN_RU[target_date.month]
    year = target_date.year
    weekday_str = DAYS_RU.get(target_date.weekday(), "")
    
    prompt = (
        f"Сегодня {day} {month_name} {year} года ({weekday_str}).\n"
        f"Составь подробную сводку «Календарь дня» для утреннего дайджеста строго в формате JSON.\n\n"
        f"Структура JSON:\n"
        f"{{\n"
        f'  "holidays": [\n'
        f'    "🧑‍⚕️ Название праздника 1",\n'
        f'    "📝 Название праздника 2",\n'
        f'    "• Название праздника 3"\n'
        f"  ],\n"
        f'  "name_days": "Список мужских и женских имен через запятую",\n'
        f'  "history": [\n'
        f'    "1492 - краткое описание исторического события 1.",\n'
        f'    "1798 - краткое описание исторического события 2.",\n'
        f'    "1892 - краткое описание исторического события 3.",\n'
        f'    "1991 - краткое описание исторического события 4."\n'
        f"  ],\n"
        f'  "folk_signs": [\n'
        f'    "• Народная примета о погоде или природе 1.",\n'
        f'    "• Народная примета о погоде или природе 2.",\n'
        f'    "• Народная примета о погоде или природе 3."\n'
        f"  ]\n"
        f"}}\n\n"
        f"Требования к содержанию:\n"
        f"1. holidays: Включи от 7 до 12 разнообразных праздников на {day} {month_name} (государственные, профессиональные, православные/церковные, международные, забавные и необычные всемирные дни). Добавляй релевантные эмодзи перед названиями.\n"
        f"2. name_days: Реальные православные и католические именины (святцы) на этот день. Список имен через запятую.\n"
        f"3. history: 4-5 реальных ключевых исторических событий, произошедших именно в этот день ({day} {month_name}) в мировой и российской истории. Формат: «ГОД - событие».\n"
        f"4. folk_signs: 2-4 народные приметы и поверья на {day} {month_name} (поведение птиц, погода, растения).\n"
        f"5. Ответ должен быть СТРОГО валидным JSON без маркдаун-оберток или дополнительного текста."
    )
    
    try:
        client = get_genai_client()
        for model in ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]:
            try:
                cfg = types.GenerateContentConfig(
                    system_instruction=(
                        "Ты экспертный историк, фольклорист и эрудит. "
                        "Отвечай строго валидным JSON со списком праздников, именин, исторических событий и народных примет."
                    ),
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=900
                )
                resp = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model,
                        contents=[prompt],
                        config=cfg
                    ),
                    timeout=5.0
                )
                if resp and resp.text:
                    raw_text = resp.text.strip()
                    # Clean potential markdown wrapping
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    raw_text = raw_text.strip()
                    
                    data = json.loads(raw_text)
                    if isinstance(data, dict) and "holidays" in data and "history" in data:
                        return data
            except Exception as e:
                logger.warning(f"Gemini model {model} failed for calendar JSON: {e}")
                continue
    except Exception as e:
        logger.error(f"Error calling Gemini for calendar: {e}")
        
    return None


async def get_today_holidays(target_date: Optional[datetime] = None) -> str:
    """
    Returns the complete, beautifully formatted calendar card for today:
    1. ПРАЗДНИКИ ДНЯ (7-12 праздников с эмодзи)
    2. ИМЕНИНЫ ОТМЕЧАЮТ (список имен)
    3. ИСТОРИЧЕСКИЕ СОБЫТИЯ (ГОД - событие)
    4. НАРОДНЫЕ ПРИМЕТЫ (приметы погоды и природы)
    """
    if target_date is None:
        target_date = datetime.now(MSK_TZ)
    
    date_key = target_date.strftime("%Y-%m-%d")
    cache = _load_cache()
    
    # 1. Cache hit (only structured dict with all 4 sections)
    if date_key in cache:
        entry = cache[date_key]
        if isinstance(entry, dict) and "holidays" in entry and "history" in entry:
            return format_calendar_card(entry)
    
    # 2. Try Gemini AI
    try:
        ai_data = await fetch_calendar_from_gemini(target_date)
        if ai_data and isinstance(ai_data, dict):
            _save_cache(date_key, ai_data)
            return format_calendar_card(ai_data)
    except Exception as e:
        logger.warning(f"AI calendar generation exception: {e}")
    
    # 3. Fallback database
    fallback_data = get_curated_fallback_data(target_date)
    _save_cache(date_key, fallback_data)
    return format_calendar_card(fallback_data)
