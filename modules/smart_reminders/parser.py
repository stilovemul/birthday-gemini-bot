import json
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from core.config import MSK_TZ
from core.gemini import get_genai_client

logger = logging.getLogger("ReminderParser")


async def parse_natural_reminder(text: str) -> Tuple[bool, Optional[datetime], Optional[str], str]:
    """
    Parses natural language reminder text into (is_valid, target_datetime, task_text, error_or_info).
    Uses Gemini AI with Moscow timezone awareness.
    """
    now_msk = datetime.now(MSK_TZ)
    current_time_str = now_msk.strftime("%Y-%m-%d %H:%M:%S (%A, MSK UTC+3)")

    # 1. Quick regex check for simple "через X минут / часов"
    rel_match = re.search(r"через\s+(\d+)\s+(минут|мин|минуты|минуту|часов|часа|час|дней|дня|день)(?:\s+(.*))?", text, re.IGNORECASE)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2).lower()
        task = (rel_match.group(3) or "").strip()
        if not task:
            # Task might be before "через"
            task = re.sub(r"через\s+\d+\s+[а-яё]+", "", text, flags=re.IGNORECASE).strip()
        task = re.sub(r"^(?:напомни|напомнить|напоминание|напоминалку)\s*", "", task, flags=re.IGNORECASE).strip()

        if "мин" in unit:
            target_dt = now_msk + timedelta(minutes=val)
        elif "час" in unit:
            target_dt = now_msk + timedelta(hours=val)
        elif "дн" in unit or "ден" in unit:
            target_dt = now_msk + timedelta(days=val)
        else:
            target_dt = now_msk + timedelta(minutes=val)

        return True, target_dt, task or "Напоминание", "OK"

    # 2. Use Gemini AI for natural language date & time parsing
    prompt = f"""Текущее время сервера (MSK UTC+3): {current_time_str}.
Пользователь написал фразу для установки напоминания:
"{text}"

Твоя задача — извлечь:
1. "task": текст того, о чем нужно напомнить (очистив от слов "напомни", "не забудь" и т.д.).
2. "datetime": точную дату и время срабатывания в формате ISO "YYYY-MM-DDTHH:MM:00". Если время суток не указано (например, просто "напомни завтра"), поставь 10:00 утра.
3. "success": true (если дату и время удалось определить) или false.

Ответь ТОЛЬКО валидным JSON без markdown-разметки:
{{"success": true, "task": "позвонить в автосервис", "datetime": "2026-09-01T15:00:00"}}
"""
    try:
        c = get_genai_client()
        response = await c.aio.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        resp_text = (response.text or "").strip()
        json_match = re.search(r"\{.*\}", resp_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            if data.get("success") and data.get("datetime"):
                dt_str = data["datetime"]
                naive_dt = datetime.fromisoformat(dt_str)
                target_dt = naive_dt.replace(tzinfo=MSK_TZ)
                task_str = data.get("task", "").strip() or "Напоминание"
                return True, target_dt, task_str, "OK"
    except Exception as e:
        logger.error(f"Gemini reminder parsing error: {e}")

    return False, None, None, "Не удалось распознать время напоминания. Примеры: <i>«Напомни завтра в 15:00 позвонить маме»</i> или <i>«Напомни через 30 минут выключить духовку»</i>"
