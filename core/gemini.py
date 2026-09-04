import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from core.config import GEMINI_API_KEY, MSK_TZ, DATA_DIR
from modules.birthdays.storage import get_sorted_birthdays, format_date_entry, format_age_word
from modules.smart_reminders.storage import get_active_reminders
from modules.food_tracker.storage import get_daily_summary
from modules.notes.handlers import load_notes
from modules.drive2_tracker.storage import get_user_drive2_config
from modules.vk_tracker.storage import get_user_vk_config
from modules.max_tracker.storage import get_user_max_config
from modules.weather_synoptic.storage import get_user_weather_config
from modules.smart_home.storage import get_user_smart_home_config
from modules.subscription_tracker.storage import get_subscription_stats
from modules.custom_rules.storage import get_user_rules

logger = logging.getLogger("GeminiEngine")

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest"
]

client = None


def get_genai_client():
    global client
    if client is None:
        client = genai.Client(api_key=GEMINI_API_KEY)
    return client


def build_full_user_context(user_id: int = 157236577) -> str:
    """
    Builds a complete real-time contextual snapshot of all user data across all bot modules:
    - Current date & time (MSK)
    - Today's and upcoming reminders
    - Family & friends birthdays (with days left and age)
    - Food & calorie intake today
    - Drive2.ru, VK, MAX messenger monitoring status
    - Smart Home devices & climate status
    - Saved notes
    - Weather location & district
    """
    now = datetime.now(MSK_TZ)
    now_str = now.strftime("%d.%m.%Y %H:%M (%A, MSK UTC+3)")
    today_date_str = now.strftime("%Y-%m-%d")

    # 1. Reminders
    reminders = get_active_reminders(user_id)
    rem_today = []
    rem_future = []
    for r in reminders:
        t_iso = r.get("target_iso", "")
        if t_iso.startswith(today_date_str):
            rem_today.append(f"• [СЕГОДНЯ в {r['target_display']}] {r['text']} (ID: {r['id']})")
        else:
            rem_future.append(f"• [{r['target_display']}] {r['text']} (ID: {r['id']})")

    if rem_today:
        reminders_section = "🔔 Напоминания на СЕГОДНЯ:\n" + "\n".join(rem_today)
        if rem_future:
            reminders_section += "\n📅 Будущие напоминания:\n" + "\n".join(rem_future[:5])
    elif rem_future:
        reminders_section = "На сегодня напоминаний нет. Будущие напоминания:\n" + "\n".join(rem_future[:5])
    else:
        reminders_section = "Активных напоминаний нет."

    # 2. Birthdays
    birthdays = get_sorted_birthdays()
    b_lines = []
    for b in birthdays:
        name = b.get("name", "")
        d_str = format_date_entry(b)
        days = b.get("days_left", 0)
        age = f", исполнится {format_age_word(b['turning_age'])}" if b.get("turning_age") else ""
        left_str = "СЕГОДНЯ!" if days == 0 else (f"завтра" if days == 1 else f"через {days} дн.")
        b_lines.append(f"• {name}: {d_str}{age} (до ДР: {left_str})")
    birthdays_section = f"Всего в базе {len(birthdays)} записей:\n" + "\n".join(b_lines) if b_lines else "Список дней рождения пуст."

    # 3. Food / Calories Today
    food = get_daily_summary(user_id)
    food_section = (
        f"Съедено сегодня ({food['date']}): {food['total_calories']} ккал из {food['goal_calories']} ккал норматива "
        f"(осталось {food['remaining_calories']} ккал). "
        f"БЖУ: Белки {food['total_protein']}г, Жиры {food['total_fat']}г, Углеводы {food['total_carbs']}г. "
        f"Приёмов пищи: {len(food.get('meals', []))}."
    )

    # 4. Drive2 Tracker
    d2 = get_user_drive2_config(user_id)
    if d2 and d2.get("cookies"):
        d2_section = f"Drive2.ru подключен 🟢 (проверка каждые 60 сек). Последние данные: сообщений {d2.get('last_messages', 0)}, уведомлений {d2.get('last_notifications', 0)}."
    else:
        d2_section = "Drive2.ru не настроен."

    # 5. VKontakte Tracker
    vk = get_user_vk_config(user_id)
    if vk and vk.get("token"):
        vk_section = f"VK подключен 🟢 ({vk.get('user_name', 'Олег')}, id{vk.get('user_id_vk', '')}). Последние данные: сообщений {vk.get('last_messages', 0)}, уведомлений {vk.get('last_notifications', 0)}."
    else:
        vk_section = "VK ожидает настройки."

    # 6. MAX Messenger Tracker
    max_cfg = get_user_max_config(user_id)
    if max_cfg and max_cfg.get("token"):
        max_section = f"MAX (web.max.ru) подключен 🟢. Последние данные: непрочитанных сообщений {max_cfg.get('last_messages', 0)}, чатов {max_cfg.get('last_unread_chats', 0)}."
    else:
        max_section = "MAX ожидает привязки токена."

    # 7. Smart Home Status
    sh_cfg = get_user_smart_home_config(user_id)
    if sh_cfg and sh_cfg.get("token"):
        sh_section = "Умный дом Яндекса подключен 🟢 (освещение, вытяжка, теплый пол, датчики климата и протечки)."
    else:
        sh_section = "Умный дом не настроен."

    # 8. Notes
    notes = load_notes()
    if notes:
        n_lines = [f"• {n['text']}" for n in notes[:6]]
        notes_section = "\n".join(n_lines)
    else:
        notes_section = "Заметок нет."

    # 9. Subscriptions
    sub_stats = get_subscription_stats(user_id)
    sub_items = sub_stats.get("items", [])
    if sub_items:
        s_lines = [f"• {s['name']}: {s['amount']} ₽/мес (след. списание: {s.get('next_payment_date')}, через {s.get('days_left')} дн.)" for s in sub_items[:5]]
        subs_section = f"Всего {len(sub_items)} подписок на сумму {sub_stats['monthly_total']} ₽/мес:\n" + "\n".join(s_lines)
    else:
        subs_section = "Активных подписок нет."

    # 10. Custom Rules
    rules = get_user_rules(user_id)
    active_r = [r for r in rules if r.get("is_active", True)]
    if active_r:
        r_lines = [f"• {r['title']}: {r['action_text']}" for r in active_r[:5]]
        rules_section = f"Активных правил ({len(active_r)}):\n" + "\n".join(r_lines)
    else:
        rules_section = "Правил нет."

    # 11. Weather
    w_cfg = get_user_weather_config(user_id)
    w_loc = f"{w_cfg.get('city', 'Санкт-Петербург')} ({w_cfg.get('district', 'Приморский р-н')})"

    # 12. Cinema Memory
    try:
        from modules.cinema_matchmaker.storage import get_user_cinema_memory
        cm_mem = get_user_cinema_memory(user_id)
        cm_watched = cm_mem.get("watched_movies", [])
        cm_liked = [w["title"] for w in cm_watched if w.get("status") == "liked"]
        cm_taste = cm_mem.get("taste_summary", "")
        if cm_liked or cm_taste:
            cinema_section = f"Вкусовой профиль: {cm_taste or 'Формируется'}. Любимые фильмы (👍): {', '.join(cm_liked[:6])}."
        else:
            cinema_section = "Профиль вкуса формируется."
    except Exception:
        cinema_section = "Формируется."

    context = f"""=== АКТУАЛЬНЫЕ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (Олег, {now_str}) ===
📍 Локация пользователя: {w_loc}

⏰ НАПОМИНАНИЯ:
{reminders_section}

🎂 ДНИ РОЖДЕНИЯ БЛИЗКИХ ({len(birthdays)} записей):
{birthdays_section}

💳 ПОДПИСКИ И РАСХОДЫ:
{subs_section}

🧩 АКТИВНЫЕ ПЕРСОНАЛЬНЫЕ ПРАВИЛА:
{rules_section}

🎬 КИНО И ВКУСОВОЙ ПРОФИЛЬ:
{cinema_section}

🥗 ПИТАНИЕ И КБЖУ СЕГОДНЯ:
{food_section}

🏠 УМНЫЙ ДОМ (ЯНДЕКС):
{sh_section}

🚗 DRIVE2.RU:
{d2_section}

🔵 ВКОНТАКТЕ (VK):
{vk_section}

💬 МЕССЕНДЖЕР MAX (web.max.ru):
{max_section}

📝 ЗАМЕТКИ:
{notes_section}
======================================================="""
    return context


def get_system_instruction(user_id: int = 157236577) -> str:
    ctx = build_full_user_context(user_id)
    birthdays = get_sorted_birthdays()
    b_count = len(birthdays)
    return f"""Ты — персональный всезнающий ИИ-ассистент Олега в Telegram (AiGemAntigravity).
Ты работаешь 24/7 автономно в облаке и имеешь прямой доступ ко всем модулям и данным бота.

{ctx}

ТВОИ ПРАВИЛА:
1. Когда Олег спрашивает про свои данные (например: "Есть ли напоминания на сегодня?", "Когда день рождения у мамы?", "Сколько калорий съел?", "Что на Drive2?", "Что в VK или MAX?", "Что с умным домом?"), ВСЕГДА бери точные факты и цифры из блока данных выше и отвечай четко, дружелюбно и по делу.
2. ВНИМАНИЕ: Количество дней рождения в базе ВСЕГДА строго равно {b_count}. Никогда не придумывай и не называй людей, которых нет в разделе '🎂 ДНИ РОЖДЕНИЯ БЛИЗКИХ'!
3. Если напоминания на сегодня есть — перечисли их с точным временем. Если нет — прямо скажи, что на сегодня задач нет, и упомяни ближайшие.
4. Отвечай на чистом русском языке, форматируй ключевые моменты жирным шрифтом и смайликами.
5. Ты умеешь поддерживать диалог на любые темы: авто, умный дом, программирование, спорт, планирование, расчеты, идеи.
"""


user_chats: Dict[int, Any] = {}


def get_or_create_chat(user_id: int, model_name: str = CANDIDATE_MODELS[0]):
    c = get_genai_client()
    sys_inst = get_system_instruction(user_id)
    if user_id not in user_chats or user_chats[user_id].get("model") != model_name:
        chat = c.aio.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
                temperature=0.7
            )
        )
        user_chats[user_id] = {"model": model_name, "chat": chat}
    return user_chats[user_id]["chat"]


def reset_chat_session(user_id: int):
    if user_id in user_chats:
        del user_chats[user_id]


async def ask_gemini(user_id: int, prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg", system_instruction: Optional[str] = None) -> str:
    c = get_genai_client()
    
    for model_name in CANDIDATE_MODELS:
        try:
            if image_bytes:
                contents = [
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt or "Что изображено на этом фото? Опиши подробно."
                ]
                cfg = types.GenerateContentConfig(
                    system_instruction=system_instruction or "Ты профессиональный ИИ-эксперт и сомелье. Внимательно анализируй изображения и следуй инструкциям пользователя."
                )
                response = await c.aio.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=cfg
                )
                if response and response.text:
                    return response.text.strip()
            else:
                sys_inst = system_instruction or get_system_instruction(user_id)
                reset_chat_session(user_id)
                chat = get_or_create_chat(user_id, model_name)
                response = await chat.send_message(prompt)
                if response and response.text:
                    return response.text.strip()
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}. Trying next candidate...")
            reset_chat_session(user_id)

    return "⏳ <b>Нейросеть Gemini сейчас испытывает кратковременную нагрузку.</b>\nПожалуйста, отправьте сообщение через 15 секунд — я сразу отвечу!"
