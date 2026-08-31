import io
import re
import json
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu
from core.gemini import ask_gemini, reset_chat_session
from modules.voice_assistant.transcriber import transcribe_audio_gemini
from modules.smart_reminders.parser import parse_natural_reminder
from modules.smart_reminders.storage import add_reminder
from modules.food_tracker.storage import log_meal, get_daily_summary
from modules.food_tracker.handlers import get_food_meal_keyboard
from modules.loan_calculator.calculator import parse_loan_query, calculate_early_repayment_savings, calculate_annuity_loan
from modules.loan_calculator.handlers import format_loan_result
from modules.birthdays.storage import add_birthday, delete_birthday, get_sorted_birthdays, format_date_entry
from modules.smart_home.storage import get_user_smart_home_config
from modules.smart_home.client import toggle_device_by_name, execute_scenario, turn_off_all_lights
from modules.weather_synoptic.service import get_weather_report
from modules.weather_synoptic.storage import get_user_weather_config
from modules.subscription_tracker.storage import add_subscription, get_subscription_stats
from modules.custom_rules.storage import add_custom_rule, get_user_rules

logger = logging.getLogger("VoiceAssistantHandler")
router = Router(name="voice_assistant")


async def _process_voice_text_action(message: types.Message, bot: Bot, text: str, user_id: int):
    """Executes corresponding bot action based on transcribed text and returns formatted response."""
    t_lower = text.lower().strip()

    # 1. Smart Home Natural Commands Trigger
    sh_toggle_match = re.match(r"^(?:включи|выключи|погаси|запусти|выруби|переключи|вырубай|вруби)\s+(.+)", text, re.IGNORECASE)
    if sh_toggle_match or any(k in t_lower for k in ["выключи свет", "включи свет", "выруби свет", "погаси свет"]):
        cfg = get_user_smart_home_config(user_id)
        sh_token = cfg.get("token") if cfg else None
        
        if sh_token:
            cmd_verb = text.split()[0].lower() if text.split() else ""
            target_obj = (sh_toggle_match.group(1).strip().lower() if sh_toggle_match else t_lower)
            is_turn_off = cmd_verb in ["выключи", "погаси", "выруби", "вырубай"] or "выключи" in t_lower or "погаси" in t_lower
            
            # Turn off all lights
            if any(w in target_obj for w in ["весь свет", "все лампы", "свет везде", "все приборы", "всё", "все"]):
                ok, res_msg, _ = await turn_off_all_lights(sh_token)
                reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n🏠 <b>Умный дом:</b> {res_msg}"""
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
            
            # Scenarios
            if "гостин" in target_obj:
                ok, res_msg = await execute_scenario(sh_token, "Свет в гостиной")
                reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n🏠 <b>Умный дом:</b> {res_msg}"""
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
            elif "барн" in target_obj:
                ok, res_msg = await execute_scenario(sh_token, "Барная стойка")
                reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n🏠 <b>Умный дом:</b> {res_msg}"""
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
                
            # Direct target devices
            target_dev = None
            if "ванн" in target_obj:
                target_dev = "Свет в ванной"
            elif "вытяжк" in target_obj:
                target_dev = "Вытяжка"
            elif "коридор" in target_obj:
                target_dev = "Свет коридор"
            elif "пол" in target_obj or "теплый" in target_obj or "тёплый" in target_obj:
                target_dev = "Теплый пол"
            else:
                target_dev = target_obj
                
            ok, res_msg, _ = await toggle_device_by_name(sh_token, target_dev, force_state=(not is_turn_off))
            if ok:
                reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n🏠 <b>Умный дом:</b> {res_msg}"""
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return

    # 2. Smart Reminders Natural NLP
    if re.match(r"^(?:напомни|напомнить|поставь\s+напоминание|сделай\s+напоминание)\s+", text, re.IGNORECASE) or "напомни" in t_lower:
        raw = re.sub(r"^(?:напомни|напомнить|поставь\s+напоминание|сделай\s+напоминание)\s*", "", text, flags=re.IGNORECASE).strip()
        success, target_dt, task_text, info_remind = await parse_natural_reminder(raw)
        if success and target_dt:
            item = add_reminder(user_id, task_text, target_dt)
            time_formatted = target_dt.strftime("%d.%m.%Y в %H:%M MSK")
            reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n✅ <b>Напоминание установлено!</b>\n📌 <b>Задача:</b> {task_text}\n🕒 <b>Время:</b> {time_formatted}\n<i>(ID: <code>{item['id']}</code>)</i>"""
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    # 3. Birthday Natural Language Add/Delete
    bday_add_match = re.match(r"^(?:добавь|запиши|сохрани|внеси)\s+(?:день\s+рождения|др)\s+(.+)", text, re.IGNORECASE)
    if bday_add_match:
        raw_bday = bday_add_match.group(1).strip()
        m = re.search(r"^(.+?)\s+(\d{1,2}(?:[./\-]\d{1,2}(?:[./\-]\d{2,4})?|\s+[а-яё]+(?:\s+\d{2,4})?))(?:\s+(.*))?$", raw_bday, re.IGNORECASE)
        if m:
            b_name = m.group(1).strip()
            b_date = m.group(2).strip()
            b_note = m.group(3).strip() if m.group(3) else ""
            success, reply_msg, _ = add_birthday(b_name, b_date, b_note)
            reset_chat_session(user_id)
            reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n{reply_msg}\n☁️ <i>Синхронизировано с облаком!</i>"""
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    # 4. Weather Voice Request
    if any(w in t_lower for w in ["какая погода", "погода", "будет ли дождь", "прогноз погоды", "синоптик", "на улице дождь"]):
        w_cfg = get_user_weather_config(user_id)
        city = w_cfg.get("city", "Санкт-Петербург")
        district = w_cfg.get("district", "Приморский р-н")
        lat = w_cfg.get("lat", 59.9950)
        lon = w_cfg.get("lon", 30.2200)
        ok, w_text = await get_weather_report(city, district, lat, lon)
        reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n{w_text}"""
        await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    # 5. Food Voice Log (e.g. "Я съел омлет и кофе", "Запиши на обед курицу с рисом")
    if any(k in t_lower for k in ["я съел", "я выпил", "съел", "выпил", "запиши еду", "запиши в рацион", "на обед", "на завтрак", "на ужин"]):
        prompt = (
            f"Пользователь голосом сообщил о приеме пищи: '{text}'. Оцени примерную калорийность и БЖУ блюда. "
            'Верни ТОЛЬКО валидный JSON в формате: {"dish_name": "Название", "calories": 350, "protein": 25.0, "fat": 12.0, "carbs": 30.0}'
        )
        ai_resp = await ask_gemini(user_id, prompt)
        try:
            m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
            if m:
                f_data = json.loads(m.group(0))
                entry = log_meal(
                    user_id=user_id,
                    dish_name=f_data.get("dish_name", text),
                    calories=int(f_data.get("calories", 200)),
                    protein=float(f_data.get("protein", 0)),
                    fat=float(f_data.get("fat", 0)),
                    carbs=float(f_data.get("carbs", 0))
                )
                summary = get_daily_summary(user_id)
                reply = f"""🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n🥗 <b>Блюдо записано в дневной рацион:</b>\n• <b>{entry['dish_name']}</b> — <b>{entry['calories']} ккал</b>\n• Б: {entry['protein']}г | Ж: {entry['fat']}г | У: {entry['carbs']}г\n\n📊 <b>Всего за день:</b> {summary['total_calories']} / {summary['goal_calories']} ккал <i>(осталось {summary['remaining_calories']} ккал)</i>"""
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
        except Exception as e:
            logger.warning(f"Voice food parse error: {e}")

    # 6. Subscriptions Voice Log (e.g. "Добавь подписку Яндекс Плюс 299 рублей 15 числа", "Сколько плачу за подписки")
    if "подписк" in t_lower:
        if any(w in t_lower for w in ["добавь", "запиши", "сохрани", "внеси"]):
            prompt = (
                f"Пользователь хочет добавить регулярную подписку голосом: '{text}'. "
                "Извлеки название сервиса, сумму в рублях, число месяца (день списания от 1 до 31) и категорию. "
                "Верни ТОЛЬКО валидный JSON в формате: "
                '{"name": "Яндекс Плюс", "amount": 299, "payment_day": 15, "category": "Медиа"}'
            )
            ai_resp = await ask_gemini(user_id, prompt)
            try:
                m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    name = data.get("name", "Подписка")
                    amount = float(data.get("amount", 300))
                    day = int(data.get("payment_day", 1))
                    cat = data.get("category", "Сервисы")
                    item = add_subscription(user_id, name, amount, day, category=cat)
                    reply = (
                        f"🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n"
                        f"💳 <b>Подписка успешно сохранена!</b>\n"
                        f"• <b>{item['name']}</b> — <b>{item['amount']} ₽/мес</b>\n"
                        f"• День списания: <b>{item['payment_day']}-е число</b> (след: <i>{item['next_payment_date']}</i>)\n\n"
                        f"🔔 Бот предупредит за 2 дня и за 1 день до списания!"
                    )
                    await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                    return
            except Exception as e:
                logger.warning(f"Voice sub parse error: {e}")
        else:
            stats = get_subscription_stats(user_id)
            reply = (
                f"🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n"
                f"💳 <b>Ваши регулярные подписки:</b>\n"
                f"• Всего сервисов: <b>{stats['total_count']} шт.</b>\n"
                f"• Общая сумма: <b>{stats['monthly_total']} ₽/мес</b> (<b>{stats['yearly_total']} ₽/год</b>)"
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    # 7. Custom Rules Voice Log (e.g. "Каждую пятницу в 18:00 напоминай...", "Каждое 20 число...")
    if any(t_lower.startswith(k) for k in ["создай правило", "добавь правило", "каждое ", "каждый ", "каждую "]):
        prompt = (
            f"Пользователь хочет создать периодическое автоматическое правило голосом: '{text}'. "
            "Определи: title (заголовок с эмодзи), trigger_type ('daily_time', 'monthly_day', 'weekly_day'), "
            "day_of_month (1-31 или 0), days_of_week (массив 0-6 где 0=Пн), hour (0-23), minute (0-59), action_text. "
            "Верни ТОЛЬКО валидный JSON: "
            '{"title": "💧 Показания счетчиков", "trigger_type": "monthly_day", "day_of_month": 20, "days_of_week": [], "hour": 12, "minute": 0, "action_text": "Пора передать показания счетчиков!"}'
        )
        ai_resp = await ask_gemini(user_id, prompt)
        try:
            m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                item = add_custom_rule(
                    user_id=user_id,
                    title=data.get("title", "Персональное правило"),
                    trigger_type=data.get("trigger_type", "daily_time"),
                    action_text=data.get("action_text", text),
                    hour=int(data.get("hour", 12)),
                    minute=int(data.get("minute", 0)),
                    day_of_month=int(data.get("day_of_month", 0)),
                    days_of_week=data.get("days_of_week", [])
                )
                reply = (
                    f"🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n"
                    f"🧩 <b>Персональное правило создано и активно!</b>\n"
                    f"📌 <b>{item['title']}</b>\n"
                    f"⏰ Время: в <b>{item['hour']:02d}:{item['minute']:02d} MSK</b>\n"
                    f"💬 Действие: {item['action_text']}"
                )
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
        except Exception as e:
            logger.warning(f"Voice rule parse error: {e}")

    # 8. Default: Intelligent Gemini Chat Answer
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ai_reply = await ask_gemini(user_id, text)
    full_reply = f"🎤 <b>Вы сказали:</b> «<i>{text}</i>»\n\n{ai_reply}"
    
    try:
        await message.answer(full_reply, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
    except Exception:
        await message.answer(full_reply, reply_markup=get_main_menu())


@router.message(F.voice)
async def handle_voice_message(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    # Download voice message
    try:
        file = await bot.get_file(message.voice.file_id)
        voice_buffer = io.BytesIO()
        await bot.download_file(file.file_path, voice_buffer)
        voice_bytes = voice_buffer.getvalue()
    except Exception as e:
        logger.error(f"Error downloading voice: {e}")
        await message.answer("⚠️ Не удалось загрузить голосовое сообщение. Попробуйте еще раз.")
        return

    # Transcribe via Gemini
    transcribed_text = await transcribe_audio_gemini(voice_bytes, mime_type="audio/ogg")
    if not transcribed_text:
        await message.answer("🎙 <i>Не удалось четко разобрать голосовое сообщение. Пожалуйста, повторите фразу.</i>", parse_mode=ParseMode.HTML)
        return

    # Process recognized text
    await _process_voice_text_action(message, bot, transcribed_text, user_id)


@router.message(F.video_note)
async def handle_video_note_message(message: types.Message, bot: Bot):
    """Handles Telegram Circles (Video notes)."""
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    try:
        file = await bot.get_file(message.video_note.file_id)
        video_buffer = io.BytesIO()
        await bot.download_file(file.file_path, video_buffer)
        video_bytes = video_buffer.getvalue()
    except Exception as e:
        logger.error(f"Error downloading video note: {e}")
        await message.answer("⚠️ Не удалось загрузить видеосообщение.")
        return

    transcribed_text = await transcribe_audio_gemini(video_bytes, mime_type="video/mp4")
    if not transcribed_text:
        await message.answer("📹 <i>Не удалось разобрать речь в видеосообщении.</i>", parse_mode=ParseMode.HTML)
        return

    await _process_voice_text_action(message, bot, transcribed_text, user_id)


@router.message(F.audio)
async def handle_audio_message(message: types.Message, bot: Bot):
    """Handles audio file uploads."""
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    try:
        file = await bot.get_file(message.audio.file_id)
        audio_buffer = io.BytesIO()
        await bot.download_file(file.file_path, audio_buffer)
        audio_bytes = audio_buffer.getvalue()
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        await message.answer("⚠️ Не удалось загрузить аудиофайл.")
        return

    mime = message.audio.mime_type or "audio/mpeg"
    transcribed_text = await transcribe_audio_gemini(audio_bytes, mime_type=mime)
    if not transcribed_text:
        await message.answer("🎵 <i>Не удалось распознать речь в аудиофайле.</i>", parse_mode=ParseMode.HTML)
        return

    await _process_voice_text_action(message, bot, transcribed_text, user_id)
