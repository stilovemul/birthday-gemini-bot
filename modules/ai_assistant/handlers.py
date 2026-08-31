import io
import re
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from core.gemini import ask_gemini, reset_chat_session
from modules.smart_reminders.parser import parse_natural_reminder
from modules.smart_reminders.storage import add_reminder
from modules.food_tracker.analyzer import analyze_food_photo
from modules.food_tracker.storage import log_meal, get_daily_summary
from modules.food_tracker.handlers import get_food_meal_keyboard
from modules.loan_calculator.calculator import parse_loan_query, calculate_early_repayment_savings, calculate_annuity_loan
from modules.loan_calculator.handlers import format_loan_result
from modules.birthdays.storage import add_birthday, delete_birthday, get_sorted_birthdays, format_date_entry
from modules.smart_home.storage import get_user_smart_home_config
from modules.smart_home.client import toggle_device_by_name, execute_scenario, turn_off_all_lights
from modules.image_gen.generator import (
    generate_image_bytes,
    refine_prompt_with_ai,
    is_user_awaiting_image,
    set_user_awaiting_image,
    start_image_session,
    update_image_session,
    end_image_session,
    is_in_image_session,
    get_image_session
)
from modules.image_gen.handlers import get_image_action_keyboard

logger = logging.getLogger("AIAssistantHandler")
router = Router(name="ai_assistant")


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    end_image_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    welcome_text = (
        "👋 <b>Привет, Олег! Супер-бот AiGemAntigravity активен 24/7!</b> 🚀\n\n"
        "Я твой персональный ИИ-ассистент в облаке с автоматической синхронизацией данных:\n\n"
        "✨ <b>Что я умею:</b>\n"
        "• 🏠 <b>Умный дом Яндекса</b>: управление светом, вытяжкой, тёплым полом и сценариями\n"
        "• 🤖 <b>Gemini AI</b>: умный диалог, ответы на любые вопросы\n"
        "• 🎨 <b>Генератор фото (RealVisXL)</b>: создание фото с сохранением внешности\n"
        "• 🥗 <b>Сканер еды & КБЖУ</b>: просто сфотографируйте вашу тарелку — я посчитаю калории, БЖУ и запишу в дневной рацион!\n"
        "• 🔢 <b>Кредитный калькулятор</b>: расчет платежа, переплаты и выгоды досрочки\n"
        "• 😴 <b>Калькулятор сна</b>: биоритмы, 90-мин циклы и Power Nap\n"
        "• 🚗 <b>Drive2.ru Монитор</b>: мгновенные алерты о сообщениях и событиях\n"
        "• 🔵 <b>VK Монитор</b>: проверка непрочитанных личных сообщений\n"
        "• 💬 <b>MAX Монитор</b>: мониторинг сообщений web.max.ru\n"
        "• 🌤 <b>Погода & Осадки</b>: радар дождя с точностью до района\n"
        "• 🔐 <b>Секретный сейф</b>: защищенное хранилище паролей и заметок\n"
        "• ⏰ <b>Умные напоминания</b>: <i>«Напомни завтра в 15:00 позвонить в банк»</i>\n"
        "• 🎂 <b>Дни рождения</b>: авто-синхронизация с облаком и напоминания в 09:00 MSK\n"
        "• 📝 <b>Заметки</b>: <code>/note Текст</code>\n\n"
        "Напишите мне что угодно или воспользуйтесь кнопками ниже 👇"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("help"))
@router.message(F.text == "❓ Справка")
async def cmd_help(message: types.Message):
    end_image_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    help_text = (
        "📖 <b>Справка по возможностям бота:</b>\n\n"
        "🏠 <b>Умный дом Яндекса:</b>\n"
        "• Кнопка «🏠 Умный дом» или напишите в чат:\n"
        "  <i>«Включи свет в ванной»</i>, <i>«Выключи вытяжку»</i>, <i>«Погаси весь свет»</i>\n\n"
        "🎂 <b>Дни рождения:</b>\n"
        "• Кнопка «🎂 Дни рождения» или напишите в чат:\n"
        "  <i>«Добавь день рождения Ивана 15 марта»</i>\n\n"
        "🥗 <b>Сканер еды и калорий:</b>\n"
        "• Отправьте фото еды в чат — бот посчитает калории, белки, жиры, углеводы и состав порции.\n"
        "• Кнопка «🥗 Сканер еды & КБЖУ» — просмотр дневного рациона и нормы.\n\n"
        "🔢 <b>Калькулятор кредитов & Ипотеки:</b>\n"
        "• <code>/credit 3 млн 18% 5 лет +10000</code>\n"
        "• Кнопка «🔢 Калькулятор кредитов» — пошаговый мастер ввода.\n\n"
        "😴 <b>Калькулятор сна:</b>\n"
        "• <code>/sleep 07:00</code> или кнопка «😴 Калькулятор сна».\n\n"
        "🎨 <b>Генерация и доработка фото:</b>\n"
        "• Кнопка «🎨 Генерация картинок» или <code>/image описание</code>\n"
        "• <b>Правки:</b> пишите любые изменения в чат подряд с сохранением лица.\n\n"
        "⏰ <b>Умные напоминания:</b>\n"
        "• <i>«Напомни завтра в 15:00 позвонить врачу»</i>\n"
        "• <code>/reminders</code> — список активных напоминаний\n\n"
        "🤖 <b>Gemini AI Диалог:</b>\n"
        "• Просто пишите любые вопросы или присылайте фото\n"
        "• <code>/clear</code> — очистить контекст диалога"
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("clear"))
@router.message(Command("reset"))
async def cmd_clear(message: types.Message):
    end_image_session(message.from_user.id)
    reset_chat_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    await message.answer("🧹 <b>Контекст очищен!</b> О чем поговорим дальше?", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(F.text == "🤖 Gemini AI")
async def cmd_gemini_info(message: types.Message):
    end_image_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    await message.answer(
        "🤖 <b>Режим общения с Gemini AI активен.</b>\n\n"
        "Просто напишите мне любой вопрос, попросите написать код, текст, план или пришлите фото — я сразу отвечу!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.message(F.photo)
async def handle_photo(message: types.Message, bot: Bot):
    end_image_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    user_id = message.from_user.id
    
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()
        caption = message.caption or ""

        # 1. Check if photo contains food (Smart Food & Calorie Scanner)
        is_food, food_data, _ = await analyze_food_photo(image_bytes, user_comment=caption)
        
        if is_food and food_data:
            dish = food_data.get("dish_name", "Блюдо")
            kcal = food_data.get("calories", 0)
            p = food_data.get("protein", 0)
            f = food_data.get("fat", 0)
            c = food_data.get("carbs", 0)
            weight = food_data.get("estimated_weight_g", 0)
            ingredients = food_data.get("ingredients", [])
            verdict = food_data.get("healthy_verdict", "")

            breakdown_lines = []
            for ing in ingredients[:5]:
                breakdown_lines.append(f"• {ing.get('name')} ({ing.get('weight', '')}): {ing.get('kcal', '')} ккал (Б:{ing.get('p')} Ж:{ing.get('f')} У:{ing.get('c')})")
            breakdown_str = "\n".join(breakdown_lines)

            entry = log_meal(user_id, dish, kcal, p, f, c, weight_g=weight, breakdown_text=breakdown_str)
            summary = get_daily_summary(user_id)

            weight_info = f"⚖️ <i>Примерный вес: ~{weight} г</i>\n" if weight else ""
            ing_info = f"📋 <b>Состав порции:</b>\n{breakdown_str}\n\n" if breakdown_str else ""
            verdict_info = f"💡 <i>{verdict}</i>\n\n" if verdict else ""

            card_text = (
                f"🥗 <b>{dish}</b>\n"
                f"{weight_info}\n"
                f"🔥 <b>Калории:</b> <code>{kcal} ккал</code>\n"
                f"🥩 <b>Белки:</b> <code>{p} г</code>\n"
                f"🧈 <b>Жиры:</b> <code>{f} г</code>\n"
                f"🍞 <b>Углеводы:</b> <code>{c} г</code>\n\n"
                f"{ing_info}"
                f"{verdict_info}"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"📊 <b>Итого за сегодня ({summary['date']}):</b>\n"
                f"🔥 <code>{summary['total_calories']} / {summary['goal_calories']} ккал</code> (осталось {summary['remaining_calories']} ккал)\n"
                f"🥩 Б: <code>{summary['total_protein']}г</code> | 🧈 Ж: <code>{summary['total_fat']}г</code> | 🍞 У: <code>{summary['total_carbs']}г</code>"
            )

            await message.answer(
                card_text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_food_meal_keyboard(entry["id"])
            )
            return

        # 2. If not food: Standard Gemini Vision Analysis
        prompt_text = caption or "Что изображено на этом фото? Опиши подробно."
        reply_text = await ask_gemini(user_id, prompt_text, image_bytes=image_bytes)
        
        try:
            await message.answer(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
        except Exception:
            await message.answer(reply_text, reply_markup=get_main_menu())

    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await message.answer(f"⚠️ Ошибка обработки фото: {e}", reply_markup=get_main_menu())


@router.message(F.text)
async def handle_generic_text(message: types.Message, bot: Bot):
    text = (message.text or "").strip()
    user_id = message.from_user.id
    t_lower = text.lower()

    # 1. Check if user is in an ACTIVE IMAGE STUDIO SESSION
    if is_in_image_session(user_id):
        if t_lower in ["⏹ закончить генерацию", "⏹ завершить", "закончить", "хватит", "стоп", "/done", "/exit", "стоп генерация"]:
            end_image_session(user_id)
            await message.answer(
                "✅ <b>Генерация завершена!</b> Итоговое фото зафиксировано.\n\n"
                "Бот вернулся в обычный режим. Чем могу помочь дальше?",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
            return
        
        if text in ["🏠 Умный дом", "🤖 Gemini AI", "🎨 Генерация картинок", "🥗 Сканер еды & КБЖУ", "⏰ Напоминания", "🎂 Дни рождения", "📝 Заметки", "❓ Справка", "😴 Калькулятор сна", "🔢 Калькулятор кредитов", "🚗 Drive2 Уведомления", "🔵 VK Уведомления", "💬 MAX Уведомления"]:
            end_image_session(user_id)
        else:
            sess = get_image_session(user_id)
            last_prompt = sess["current_en_prompt"] if sess else text
            locked_seed = sess.get("seed") if sess else None
            
            status_msg = await message.answer(f"🎨 <i>Вношу правку: «{text}» в текущее фото...</i>", parse_mode=ParseMode.HTML)
            await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            
            refined_prompt = await refine_prompt_with_ai(last_prompt, text)
            success, img_bytes, orig_p, en_p, seed_used = await generate_image_bytes(
                refined_prompt,
                user_id=user_id,
                is_already_en=True,
                seed=locked_seed
            )
            
            try:
                await status_msg.delete()
            except Exception:
                pass
                
            if success and img_bytes:
                update_image_session(user_id, text, refined_prompt)
                photo_file = BufferedInputFile(img_bytes, filename="studio_edit.jpg")
                caption = (
                    f"🎨 <b>Фото обновлено!</b>\n"
                    f"📝 <i>Правка:</i> «{text}»\n\n"
                    "💡 <i>Продолжайте писать точечные правки в чат или используйте кнопки ниже:</i>"
                )
                await message.answer_photo(
                    photo_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_image_action_keyboard()
                )
                return
            else:
                await message.answer(f"❌ {en_p}", reply_markup=get_image_action_keyboard())
                return

    # 2. Check if user is in "Awaiting Image Prompt" mode
    if is_user_awaiting_image(user_id):
        set_user_awaiting_image(user_id, False)
        status_msg = await message.answer(f"🎨 <i>Генерирую фото «{text}»... (3-5 сек)</i>", parse_mode=ParseMode.HTML)
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        success, img_bytes, orig_p, en_p, seed_used = await generate_image_bytes(text, user_id=user_id)
        try:
            await status_msg.delete()
        except Exception:
            pass
        if success and img_bytes:
            start_image_session(user_id, orig_p, en_p, seed=seed_used)
            photo_file = BufferedInputFile(img_bytes, filename="art.jpg")
            caption = (
                f"✨ <b>Запрос:</b> «<i>{orig_p}</i>»\n\n"
                "💡 <b>Режим точечных правок:</b> пишите любые изменения в чат."
            )
            await message.answer_photo(photo_file, caption=caption, parse_mode=ParseMode.HTML, reply_markup=get_image_action_keyboard())
            return
        else:
            await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())
            return

    # 3. Direct image generation triggers
    image_prefix_match = re.match(r"^(?:изображение|картинка|фото|арт|рисунок):\s*(.+)", text, re.IGNORECASE)
    draw_match = re.match(r"^(?:нарисуй|сгенерируй\s+картинку|сделай\s+картинку|нарисуй\s+мне|нарисуйте|нарисуй\s+пожалуйста)\s+(.+)", text, re.IGNORECASE)
    is_standalone_photo_prompt = bool(re.search(r"\b(?:реальное\s+фото|портрет|фотография|digital\s+art|арт)\b", text, re.IGNORECASE) and len(text) < 120 and not text.endswith("?"))

    if image_prefix_match or draw_match or is_standalone_photo_prompt:
        if image_prefix_match:
            prompt = image_prefix_match.group(1).strip()
        elif draw_match:
            prompt = draw_match.group(1).strip()
        else:
            prompt = text

        status_msg = await message.answer(f"🎨 <i>Генерирую фото «{prompt}»...</i>", parse_mode=ParseMode.HTML)
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        success, img_bytes, orig_p, en_p, seed_used = await generate_image_bytes(prompt, user_id=user_id)
        try:
            await status_msg.delete()
        except Exception:
            pass
        if success and img_bytes:
            start_image_session(user_id, orig_p, en_p, seed=seed_used)
            photo_file = BufferedInputFile(img_bytes, filename="art.jpg")
            caption = (
                f"✨ <b>Запрос:</b> «<i>{orig_p}</i>»\n\n"
                "💡 <b>Режим точечных правок активен:</b> пишите любые изменения в чат."
            )
            await message.answer_photo(photo_file, caption=caption, parse_mode=ParseMode.HTML, reply_markup=get_image_action_keyboard())
            return
        else:
            await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())
            return

    # 4. Smart Home Natural Commands Trigger
    sh_toggle_match = re.match(r"^(?:включи|выключи|погаси|запусти|выруби|переключи)\s+(.+)", text, re.IGNORECASE)
    if sh_toggle_match:
        cfg = get_user_smart_home_config(user_id)
        sh_token = cfg.get("token") if cfg else None
        
        if sh_token:
            cmd_verb = text.split()[0].lower()
            target_obj = sh_toggle_match.group(1).strip().lower()
            is_turn_off = cmd_verb in ["выключи", "погаси", "выруби"]
            
            # Turn off all lights
            if any(w in target_obj for w in ["весь свет", "все лампы", "свет везде", "все приборы"]):
                ok, res_msg, _ = await turn_off_all_lights(sh_token)
                await message.answer(f"🏠 {res_msg}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
            
            # Scenarios
            if "гостин" in target_obj:
                ok, res_msg = await execute_scenario(sh_token, "Свет в гостиной")
                await message.answer(f"🏠 {res_msg}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
            elif "барн" in target_obj:
                ok, res_msg = await execute_scenario(sh_token, "Барная стойка")
                await message.answer(f"🏠 {res_msg}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
                
            # Direct target devices
            target_dev = None
            if "ванн" in target_obj and ("свет" in target_obj or "ламп" in target_obj or "выключател" in target_obj):
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
                await message.answer(f"🏠 {res_msg}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return

    # 5. Birthday Natural Language Add/Delete Triggers (Direct Cloud-Synced DB execution)
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
            cloud_info = "\n☁️ <i>Запись моментально синхронизирована с облаком!</i>" if success else ""
            await message.answer(f"{reply_msg}{cloud_info}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    bday_del_match = re.match(r"^(?:удали|сотри|убери)\s+(?:день\s+рождения|др)\s+(.+)", text, re.IGNORECASE)
    if bday_del_match:
        raw_target = bday_del_match.group(1).strip()
        success, reply_msg = delete_birthday(raw_target)
        reset_chat_session(user_id)
        cloud_info = "\n☁️ <i>Изменения синхронизированы с облаком!</i>" if success else ""
        await message.answer(f"{reply_msg}{cloud_info}", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    # 6. Smart Reminders Natural NLP
    if re.match(r"^(?:напомни|напомнить|поставь\s+напоминание|сделай\s+напоминание)\s+", text, re.IGNORECASE):
        raw = re.sub(r"^(?:напомни|напомнить|поставь\s+напоминание|сделай\s+напоминание)\s*", "", text, flags=re.IGNORECASE).strip()
        success, target_dt, task_text, info_remind = await parse_natural_reminder(raw)
        if success and target_dt:
            item = add_reminder(user_id, task_text, target_dt)
            time_formatted = target_dt.strftime("%d.%m.%Y в %H:%M MSK")
            reply = (
                f"✅ <b>Напоминание установлено!</b>\n\n"
                f"📌 <b>Задача:</b> {task_text}\n"
                f"🕒 <b>Время:</b> {time_formatted}\n"
                f"<i>(ID: <code>{item['id']}</code>)</i>"
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    # 7. Loan / Credit Calculation Explicit Trigger (only on explicit calculation intent)
    if any(k in t_lower for k in ["посчитай кредит", "рассчитай кредит", "посчитай ипотек", "рассчитай ипотек", "калькулятор кредит", "калькулятор ипотек", "досрочн", "переплат", "посчитай займ"]):
        parsed = parse_loan_query(text)
        if parsed:
            amount, rate, months, extra = parsed
            if extra > 0:
                res = calculate_early_repayment_savings(amount, rate, months, extra_monthly=extra)
            else:
                res = calculate_annuity_loan(amount, rate, months)

            reply = format_loan_result(res)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="➕ Досрочка +5 000 ₽/мес", callback_data=f"ln_add_5000_{int(amount)}_{rate}_{months}"),
                        InlineKeyboardButton(text="➕ +15 000 ₽/мес", callback_data=f"ln_add_15000_{int(amount)}_{rate}_{months}")
                    ],
                    [
                        InlineKeyboardButton(text="✏️ Ввести другие параметры", callback_data="ln_wizard_start")
                    ]
                ]
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=kb)
            return

    # 8. Subscriptions & Recurring Payments Multi-Item Natural NLP (Supports Mortgage, Rent, Loans, Media, Telecom)
    is_sub_candidate = (
        any(k in t_lower for k in ["подписк", "подписку", "подписки", "списание", "каждый месяц", "ежемесячно", "абонентск", "тариф", "рублей, каждый месяц"]) or
        bool(re.search(r"\b(?:\d{1,2}\s+(?:янв|фев|мар|апр|ма|июн|июл|авг|сен|окт|ноя|дек|числа)|числа\s+\d{1,2})\b.*\b\d{2,5}\b", t_lower)) or
        bool(re.search(r"\b\d{2,5}\s*(?:руб|р|₽|\.00|\.50|\.5)\b.*\b\d{1,2}\b", t_lower))
    )

    if is_sub_candidate and not any(k in t_lower for k in ["погода", "напомни"]):
        from modules.subscription_tracker.storage import add_subscription, get_subscription_stats
        prompt = (
            f"Пользователь отправил список регулярных подписок / платежей:\n'{text}'\n\n"
            "Твоя задача — извлечь ВСЕ подписки и регулярные платежи в массив объектов. "
            "Для каждой подписки определи: "
            "- name: название сервиса/платежа (например: 'Яндекс Плюс', 'Ростелеком', 'Мегафон') "
            "- amount: сумма списания в рублях (число, например 449, 899, 163) "
            "- payment_day: день месяца списания от 1 до 31 (число, например 10, 12, 25) "
            "- category: категория ('Медиа & Музыка', 'Связь & Интернет', 'Дом', 'Сервисы') "
            "Верни ТОЛЬКО валидный JSON в формате:\n"
            '{"is_subscriptions": true, "items": [{"name": "Яндекс Плюс", "amount": 449, "payment_day": 10, "category": "Медиа & Музыка"}, {"name": "Ростелеком", "amount": 899, "payment_day": 12, "category": "Интернет & ТВ"}]}'
        )
        ai_resp = await ask_gemini(user_id, prompt)
        try:
            import json
            m = re.search(r"\{.*\}", ai_resp, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                items = data.get("items", [])
                if items and isinstance(items, list):
                    added_items = []
                    for it in items:
                        name = it.get("name", "Подписка")
                        amount = float(it.get("amount", 300))
                        day = int(it.get("payment_day", 1))
                        cat = it.get("category", "Сервисы")
                        added = add_subscription(user_id, name, amount, day, category=cat)
                        added_items.append(added)

                    reset_chat_session(user_id)
                    stats = get_subscription_stats(user_id)

                    lines = [
                        f"✅ <b>Успешно сохранено в базу данных: {len(added_items)} шт.!</b>\n"
                    ]
                    for idx, it in enumerate(added_items, 1):
                        lines.append(f"{idx}. <b>{it['name']}</b> — <b>{it['amount']} ₽/мес</b> (<i>{it['payment_day']}-е число</i>, {it['category']})")

                    lines.append(f"\n📊 <b>Всего расходов:</b> <b>{stats['monthly_total']} ₽/мес</b> (<b>{stats['yearly_total']} ₽/год</b>)")
                    lines.append("🔔 <i>Бот автоматически предупредит за 2 дня и за 1 день до каждого списания!</i>")
                    lines.append("☁️ <i>Данные сохранены и синхронизированы с GitHub облаком!</i>")

                    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                    return
        except Exception as e:
            logger.warning(f"Error in multi-sub NLP parser: {e}")

    # 9. Custom Rules & Periodic Tasks Natural NLP (with Date Range support)
    is_rule_candidate = (
        any(k in t_lower for k in ["создай правило", "добавь правило", "новое правило", "каждое ", "каждый ", "каждую ", "ежемесячно", "еженедельно"]) or
        ("показания" in t_lower and ("числа" in t_lower or "по" in t_lower or "счетчик" in t_lower)) or
        bool(re.search(r"с\s+\d{1,2}\s+(?:числа\s+)?по\s+\d{1,2}", t_lower))
    )

    if is_rule_candidate and not any(k in t_lower for k in ["подписк", "кредит", "ипотек", "погода"]):
        from modules.custom_rules.storage import add_custom_rule
        prompt = (
            f"Пользователь хочет создать персональное периодическое правило / повторяющуюся задачу:\n'{text}'\n\n"
            "Определи параметры правила: "
            "1. title: Короткий заголовок с понятным эмодзи (до 30 символов, например '💧 Передать показания счетчиков'). "
            "2. trigger_type: "
            "   - 'monthly_range' (если указан диапазон дат каждого месяца, например 'с 20 по 24 число') "
            "   - 'monthly_day' (если точный один день месяца, например '20-е число') "
            "   - 'weekly_day' (если определенный день недели, например 'каждую пятницу') "
            "   - 'daily_time' (если каждый день) "
            "3. start_day: начальное число диапазона от 1 до 31 (число, например 20, если monthly_range, иначе 0). "
            "4. end_day: конечное число диапазона от 1 до 31 (число, например 24, если monthly_range, иначе 0). "
            "5. day_of_month: число месяца (если monthly_day или start_day). "
            "6. days_of_week: массив чисел от 0 до 6, где 0=Пн, 4=Пт, 6=Вс (если weekly_day). "
            "7. hour: час напоминания от 0 до 23 (по умолчанию 12). "
            "8. minute: минуты от 0 до 59 (по умолчанию 0). "
            "9. action_text: Понятный текст напоминания / инструкции. "
            "Верни ТОЛЬКО валидный JSON в формате:\n"
            '{"title": "💧 Передать показания счетчиков", "trigger_type": "monthly_range", "start_day": 20, "end_day": 24, "day_of_month": 20, "days_of_week": [], "hour": 12, "minute": 0, "action_text": "Пора передать показания счетчиков воды и света!"}'
        )
        ai_resp = await ask_gemini(user_id, prompt)
        try:
            import json
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
                    start_day=int(data.get("start_day", 0)),
                    end_day=int(data.get("end_day", 0)),
                    day_of_month=int(data.get("day_of_month", 0)),
                    days_of_week=data.get("days_of_week", [])
                )
                reset_chat_session(user_id)
                h_str = f"{item['hour']:02d}:{item['minute']:02d} MSK"
                tt = item.get("trigger_type")
                if tt == "monthly_range":
                    sched_desc = f"каждый месяц с {item.get('start_day')} по {item.get('end_day')} число"
                elif tt == "monthly_day":
                    sched_desc = f"каждое {item.get('day_of_month')}-е число"
                elif tt == "weekly_day":
                    sched_desc = "еженедельно"
                else:
                    sched_desc = "ежедневно"

                reply = (
                    f"✅ <b>Персональное правило и задача созданы!</b>\n\n"
                    f"📌 <b>{item['title']}</b>\n"
                    f"🗓 <b>Период:</b> {sched_desc} (в {h_str})\n"
                    f"💬 <b>Действие:</b> {item['action_text']}\n"
                    f"👉 <b>Статус:</b> ⚪️ <i>Ожидает выполнения</i>\n\n"
                    f"🔔 <i>Бот будет напоминать в этот период, пока вы не нажмете зеленый значок 🟢 [Выполнено] в боте!</i>\n"
                    f"☁️ <i>Правило синхронизировано с GitHub облаком и добавлено в «⏰ Напоминания»!</i>"
                )
                await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                return
        except Exception as e:
            logger.warning(f"Error parsing rule NLP in ai_assistant: {e}")

    # 10. Default: General Gemini AI conversation
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ai_reply = await ask_gemini(user_id, text)
    
    try:
        await message.answer(ai_reply, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
    except Exception as e:
        logger.warning(f"Markdown send failed: {e}. Sending plain text...")
        await message.answer(ai_reply, reply_markup=get_main_menu())
