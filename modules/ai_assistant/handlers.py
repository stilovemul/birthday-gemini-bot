import io
import re
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.types import BufferedInputFile
from core.keyboards import get_main_menu
from core.gemini import ask_gemini, reset_chat_session
from modules.smart_reminders.parser import parse_natural_reminder
from modules.smart_reminders.storage import add_reminder
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
        "Я твой персональный ИИ-ассистент в облаке с кучей полезных функций:\n\n"
        "✨ <b>Что я умею:</b>\n"
        "• 🤖 <b>Gemini AI</b>: живой умный диалог, ответы на любые вопросы\n"
        "• 🎨 <b>Генератор фото (RealVisXL)</b>: напишите <code>/image описание</code> или нажмите кнопку в меню\n"
        "  └ <i>Точечные правки: пока активна сессия, пишите любые правки — бот будет изменять именно текущее фото, не меняя человека, пока вы не нажмете кнопку «🔄 Сгенерировать НОВОЕ изображение» или «⏹ Закончить»!</i>\n"
        "• ⏰ <b>Умные напоминания</b>: <i>«Напомни завтра в 15:00 позвонить в банк»</i>\n"
        "• 🎂 <b>Дни рождения</b>: авто-напоминания в 09:00 MSK\n"
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
        "🎨 <b>Генерация и точечная доработка фото:</b>\n"
        "• Кнопка «🎨 Генерация картинок» или <code>/image описание</code>\n"
        "• <b>Правки:</b> пишите любые изменения в чат подряд. Бот будет модифицировать то же самое фото (с сохранением внешности), пока вы не нажмете «⏹ Закончить генерацию» или «🔄 Сгенерировать НОВОЕ изображение».\n\n"
        "⏰ <b>Умные напоминания:</b>\n"
        "• <i>«Напомни завтра в 15:00 позвонить врачу»</i>\n"
        "• <i>«Напомни через 30 минут выпить таблетку»</i>\n"
        "• <code>/reminders</code> — список всех активных напоминаний\n\n"
        "🤖 <b>Gemini AI Диалог:</b>\n"
        "• Просто пишите любые вопросы или присылайте фото\n"
        "• <code>/clear</code> — очистить контекст диалога\n\n"
        "🎂 <b>Дни рождения:</b>\n"
        "• <code>/add Имя ДД.ММ.ГГГГ [Заметка]</code> | <code>/list</code>\n\n"
        "📝 <b>Заметки:</b> <code>/note Текст</code> | <code>/notes</code>"
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
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await bot.download(photo, destination=file_io)
        image_bytes = file_io.getvalue()

        caption = message.caption or "Что изображено на этом фото?"
        reply_text = await ask_gemini(message.from_user.id, caption, image_bytes=image_bytes)
        
        try:
            await message.answer(reply_text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
        except Exception:
            await message.answer(reply_text, reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await message.answer(f"⚠️ Ошибка анализа фото: {e}", reply_markup=get_main_menu())


@router.message(F.text)
async def handle_generic_text(message: types.Message, bot: Bot):
    text = (message.text or "").strip()
    user_id = message.from_user.id
    t_lower = text.lower()

    # 1. Check if user is in an ACTIVE IMAGE STUDIO SESSION
    if is_in_image_session(user_id):
        # Exit triggers
        if t_lower in ["⏹ закончить генерацию", "⏹ завершить", "закончить", "хватит", "стоп", "/done", "/exit", "стоп генерация"]:
            end_image_session(user_id)
            await message.answer(
                "✅ <b>Генерация завершена!</b> Итоговое фото зафиксировано.\n\n"
                "Бот вернулся в обычный режим. Чем могу помочь дальше?",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
            return
        
        # Menu buttons exit session and continue to menu
        if text in ["🤖 Gemini AI", "🎨 Генерация картинок", "⏰ Напоминания", "🎂 Дни рождения", "📝 Заметки", "❓ Справка"]:
            end_image_session(user_id)
        else:
            # Modify the EXACT same image preserving Seed!
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
                    "💡 <i>Продолжайте писать точечные правки в чат или нажмите кнопку ниже для завершения:</i>"
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

    # 2. Check if user is in "Awaiting Image Prompt" mode (after clicking button)
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
                "💡 <b>Режим точечных правок:</b> пишите любые изменения в чат.\n"
                "<i>(Бот правит это фото без сброса внешности, пока вы не нажмете «Сгенерировать НОВОЕ изображение» или «Закончить»).</i>"
            )
            await message.answer_photo(photo_file, caption=caption, parse_mode=ParseMode.HTML, reply_markup=get_image_action_keyboard())
            return
        else:
            await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())
            return

    # 3. Check direct image commands / prefixes
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
                "💡 <b>Режим точечных правок активен:</b> пишите любые изменения в чат.\n"
                "<i>(Бот правит это фото без сброса внешности, пока вы не нажмете «Сгенерировать НОВОЕ изображение» или «Закончить»).</i>"
            )
            await message.answer_photo(photo_file, caption=caption, parse_mode=ParseMode.HTML, reply_markup=get_image_action_keyboard())
            return
        else:
            await message.answer(f"❌ {en_p}", reply_markup=get_main_menu())
            return

    # 4. Smart Reminders: "напомни...", "поставь напоминание..."
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

    # 5. Default: General Gemini AI conversation
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ai_reply = await ask_gemini(user_id, text)
    
    try:
        await message.answer(ai_reply, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
    except Exception as e:
        logger.warning(f"Markdown send failed: {e}. Sending plain text...")
        await message.answer(ai_reply, reply_markup=get_main_menu())
