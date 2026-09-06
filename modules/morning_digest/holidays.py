import os
import json
import logging
import asyncio
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from core.config import MSK_TZ, DATA_DIR, GEMINI_API_KEY
from core.gemini import get_genai_client, CANDIDATE_MODELS
from google.genai import types

logger = logging.getLogger("TodayHolidays")

CACHE_FILE = os.path.join(DATA_DIR, "holidays_cache.json")
_holidays_memory_cache: Dict[str, str] = {}

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

# Extensive curated calendar of Russian state, professional, international, and famous fun holidays
CURATED_HOLIDAYS_CALENDAR = {
    (1, 1): [
        "🇷🇺 <b>Новый год</b> — главный всенародный праздник",
        "🌍 <b>Всемирный день мира</b> (День всемирных молитв о мире)",
        "🎉 <b>День былинного богатыря Ильи Муромца</b>"
    ],
    (1, 7): [
        "⭐️ <b>Рождество Христово</b> — один из главных праздников",
        "🌍 <b>Международный день программистов</b> (неофициальный)"
    ],
    (1, 14): [
        "🎄 <b>Старый Новый год</b> — уникальная традиция",
        "🛢 <b>День трубопроводных войск России</b>"
    ],
    (1, 25): [
        "🎓 <b>Татьянин день (День российского студенчества)</b>",
        "⛄️ <b>День счастливых снеговиков</b>"
    ],
    (2, 14): [
        "❤️ <b>День святого Валентина (День всех влюбленных)</b>",
        "💻 <b>День компьютерщика</b> (запуск ENIAC в 1946 году)",
        "📚 <b>Международный день книгодарения</b>"
    ],
    (2, 23): [
        "🇷🇺 <b>День защитника Отечества</b> — государственный праздник",
        "🍌 <b>Всемирный день бананового хлеба</b>"
    ],
    (3, 8): [
        "💐 <b>Международный женский день</b> — весенний государственный праздник",
        "🥞 <b>День весеннего тепла и красоты</b>"
    ],
    (3, 20): [
        "☀️ <b>Международный день счастья</b>",
        "🌱 <b>День весеннего равноденствия</b>",
        "🌍 <b>День Земли</b>"
    ],
    (4, 1): [
        "😄 <b>День смеха (День дурака)</b> — день добрых розыгрышей",
        "🦅 <b>Международный день птиц</b>"
    ],
    (4, 12): [
        "🚀 <b>День космонавтики</b> — триумф Юрия Гагарина в 1961 году",
        "🌍 <b>Всемирный день авиации и космонавтики</b>"
    ],
    (5, 1): [
        "🌷 <b>Праздник Весны и Труда</b> — государственный выходной",
        "🌻 <b>День подсолнуха</b>"
    ],
    (5, 9): [
        "🎖 <b>День Победы</b> — 9 Мая, великий всенародный праздник",
        "🎗 <b>День воинской славы России</b>"
    ],
    (6, 1): [
        "👶 <b>Международный день защиты детей</b> — начало лета",
        "🥛 <b>Всемирный день молока</b>"
    ],
    (6, 6): [
        "📖 <b>Пушкинский день (День русского языка)</b>",
        "✍️ <b>День рождения А. С. Пушкина</b>"
    ],
    (6, 12): [
        "🇷🇺 <b>День России</b> — главный государственный праздник страны",
        "🕊 <b>День принятия Декларации о государственном суверенитете РФ</b>"
    ],
    (7, 8): [
        "👨‍👩‍👧 <b>День семьи, любви и верности (День Петра и Февронии)</b>",
        "🌿 <b>День зенитно-ракетных войск РФ</b>"
    ],
    (8, 2): [
        "🪂 <b>День Воздушно-десантных войск (ВДВ)</b>",
        "🍉 <b>Всемирный день арбуза</b>"
    ],
    (8, 22): [
        "🇷🇺 <b>День Государственного флага Российской Федерации</b>",
        "🪴 <b>День растительного молока</b>"
    ],
    (9, 1): [
        "🔔 <b>День знаний</b> — начало нового учебного года",
        "🍂 <b>Первый день осени</b>"
    ],
    (9, 6): [
        "✈️ <b>День полётов над землёй</b> — праздник мечтателей и романтиков",
        "📚 <b>Всемирный день чтения книг (Read a Book Day)</b>",
        "👩‍🦰 <b>Всемирный день рыжих людей</b>",
        "🛡 <b>День подразделений по противодействию экстремизму МВД РФ</b>"
    ],
    (9, 13): [
        "💻 <b>День программиста в России</b> (256-й день года)",
        "💇 <b>День парикмахера в России</b>",
        "🍫 <b>Международный день шоколада</b>"
    ],
    (10, 5): [
        "👩‍🏫 <b>День учителя в России</b> (World Teachers' Day)",
        "🕵️ <b>День работников уголовного розыска России</b>"
    ],
    (10, 31): [
        "🎃 <b>Хэллоуин (Канун Дня всех святых)</b>",
        "🌊 <b>Международный день Черного моря</b>",
        "🧙‍♂️ <b>День магии и фокусов</b>"
    ],
    (11, 4): [
        "🇷🇺 <b>День народного единства</b> — государственный праздник России",
        "🕊 <b>День Казанской иконы Божией Матери</b>"
    ],
    (12, 31): [
        "🍾 <b>Канун Нового года</b> — подготовка к праздничной ночи",
        "✨ <b>День исполнения заветных желаний</b>",
        "🎉 <b>День троп и дорожек</b>"
    ]
}


def _load_cache() -> Dict[str, str]:
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


def _save_cache(date_key: str, text: str):
    global _holidays_memory_cache
    _holidays_memory_cache[date_key] = text
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_holidays_memory_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Error saving holidays cache: {e}")


def get_curated_fallback_holidays(target_date: datetime) -> str:
    """Returns curated fallback holidays based on day and month."""
    key = (target_date.month, target_date.day)
    if key in CURATED_HOLIDAYS_CALENDAR:
        items = CURATED_HOLIDAYS_CALENDAR[key]
        return "\n".join(f"• {item}" if not item.startswith("•") else item for item in items)
    
    # Generic dynamic fallbacks if day not specifically mapped
    d_num = target_date.day
    m_name = MONTHS_GEN_RU[target_date.month]
    weekday_idx = target_date.weekday()
    
    items = []
    # Check 256th day for programmer day
    day_of_year = target_date.timetuple().tm_yday
    if day_of_year == 256:
        items.append("💻 <b>День программиста</b> — 256-й день года!")
    
    # Sunday / Weekend / Friday specials
    if weekday_idx == 6:
        items.append(f"☀️ <b>Воскресный день отдыха и семьи</b> — отличный повод набраться сил")
    elif weekday_idx == 4:
        items.append(f"🎉 <b>Пятница</b> — завершение рабочей недели")
        
    items.append(f"📅 <b>День {d_num} {m_name}</b> — прекрасный повод для новых свершений и хорошего настроения")
    items.append(f"☕️ <b>Всемирный день приятных моментов</b> — уделите время себе и близким")
    
    return "\n".join(f"• {item}" for item in items)


async def fetch_holidays_from_gemini(target_date: datetime) -> Optional[str]:
    """Generates a rich, accurate list of today's holidays via Gemini."""
    day = target_date.day
    month_name = MONTHS_GEN_RU[target_date.month]
    year = target_date.year
    weekday_str = DAYS_RU.get(target_date.weekday(), "")
    
    prompt = (
        f"Сегодня {day} {month_name} {year} года, {weekday_str}.\n"
        f"Назови, какие сегодня праздники в России и в мире (государственные, профессиональные, международные, а также необычные или забавные всемирные праздники).\n\n"
        f"Требования к ответу:\n"
        f"1. Выбери ТОП 3-5 самых ярких, официальных и интересных праздников на этот конкретный день ({day} {month_name}).\n"
        f"2. Обязательно включи официальные/профессиональные праздники РФ, если они есть в эту дату, плюс 1-2 интересных всемирных/необычных дня.\n"
        f"3. Формат каждого пункта СТРОГО: «• [Эмодзи] <b>Название праздника</b> — краткое пояснение или факт в 1 строку» (если название говорит само за себя, тире и пояснение можно сделать ультракратким).\n"
        f"4. Запрещено писать вступительные слова («Вот список...», «Сегодня отмечаются:») и заключительные фразы. Только сам список из 3-5 строк через «• ».\n"
        f"5. Используй только валидный Telegram HTML (теги <b>, <i>, <code>). Не используй markdown-звёздочки **."
    )
    
    try:
        client = get_genai_client()
        for model in ["gemini-3.7-flash", "gemini-3.5-flash"]:
            try:
                cfg = types.GenerateContentConfig(
                    system_instruction=(
                        "Ты экспертный календарный эрудит и ведущий утреннего дайджеста. "
                        "Твоя задача — выдавать точный, красивый и позитивный список сегодняшних праздников в строгом формате списка Telegram HTML."
                    ),
                    temperature=0.3,
                    max_output_tokens=400
                )
                resp = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model,
                        contents=[prompt],
                        config=cfg
                    ),
                    timeout=4.0
                )
                if resp and resp.text:
                    text = resp.text.strip()
                    # Sanitize: convert markdown bold to HTML if any leaked
                    text = text.replace("**", "<b>").replace("**", "</b>")
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    cleaned_lines = []
                    for l in lines:
                        if not l.startswith("•") and not l.startswith("-") and not l.startswith("*"):
                            l = f"• {l}"
                        elif l.startswith("- ") or l.startswith("* "):
                            l = f"• {l[2:]}"
                        cleaned_lines.append(l)
                    
                    if len(cleaned_lines) >= 2:
                        return "\n".join(cleaned_lines[:5])
            except Exception as e:
                logger.warning(f"Gemini model {model} failed for holidays: {e}")
                continue
    except Exception as e:
        logger.error(f"Error fetching holidays from Gemini: {e}")
    
    return None


async def get_today_holidays(target_date: Optional[datetime] = None) -> str:
    """
    Returns today's holidays formatted in Telegram HTML.
    Utilizes daily file/memory caching, Gemini AI curation, and curated offline calendar fallback.
    """
    if target_date is None:
        target_date = datetime.now(MSK_TZ)
    
    date_key = target_date.strftime("%Y-%m-%d")
    cache = _load_cache()
    
    # 1. Return from cache if already generated today
    if date_key in cache and cache[date_key].strip():
        return cache[date_key]
    
    # 2. Try Gemini AI Generation
    try:
        ai_holidays = await fetch_holidays_from_gemini(target_date)
        if ai_holidays and len(ai_holidays.strip()) > 15:
            _save_cache(date_key, ai_holidays)
            return ai_holidays
    except Exception as e:
        logger.warning(f"Gemini holidays generation exception: {e}")
    
    # 3. Offline Curated Fallback Calendar
    fallback = get_curated_fallback_holidays(target_date)
    _save_cache(date_key, fallback)
    return fallback
