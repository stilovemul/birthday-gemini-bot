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
from modules.image_gen.generator import generate_image_bytes

logger = logging.getLogger("AIAssistantHandler")
router = Router(name="ai_assistant")


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 <b>Привет, Олег! Супер-бот AiGemAntigravity активен 24/7!</b> 🚀\n\n"
        "Я твой персональный ИИ-ассистент в облаке с кучей полезных функций:\n\n"
        "✨ <b>Что я умею прямо сейчас:</b>\n"
        "• 🤖 <b>Gemini AI</b>: живой умный диалог, решение любых задач\n"
        "• 🎨 <b>Генерация картинок</b>: напишите <code>/image описание</code> или просто <i>«Нарисуй кота в космосе»</i>\n"
        "• ⏰ <b>Умные напоминания</b>: <i>«Напомни завтра в 15:00 позвонить в банк»</i> или <i>«Напомни через 40 мин выключить духовку»</i>\n"
        "• 🎂 <b>Дни рождения</b>: напоминания в 09:00 MSK (за 7, 3, 1 день и в праздник)\n"
        "• 📝 <b>Заметки</b>: <code>/note Текст</code>\n\n"
        "Напишите мне что угодно или воспользуйтесь кнопками ниже 👇"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("help"))
@router.message(F.text == "❓ Справка")
async def cmd_help(message: types.Message):
    help_text = (
        "📖 <b>Справка по возможностям бота:</b>\n\n"
        "🎨 <b>Генерация картинок:</b>\n"
        "• <code>/image спорткар на закате</code> или <i>«Нарисуй кота в очках»</i>\n\n"
        "⏰ <b>Умные напоминания:</b>\n"
        "• <i>«Напомни завтра в 15:00 позвонить врачу»</i>\n"
        "• <i>«Напомни через 30 минут выпить таблетку»</i>\n"
        "• <code>/reminders</code> — список всех активных напоминаний\n\n"
        "🤖 <b>Gemini AI Диалог:</b>\n"
        "• Просто пишите любые вопросы или присылайте фото\n"
        "• <code>/clear</code> — очистить контекст диалога\n\n"
        "🎂 <b>Дни рождения:</b>\n"
        "• <code>/add Имя ДД.ММ.ГГГГ [Заметка]</code>\n"
        "• <code>/list</code> — список всех именинников\n\n"
        "📝 <b>Быстрые заметки:</b>\n"
        "• <code>/note Текст</code> | <code>/notes</code>"
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("clear"))
@router.message(Command("reset"))
async def cmd_clear(message: types.Message):
    reset_chat_session(message.from_user.id)
    await message.answer("🧹 <b>Контекст диалога очищен!</b> О чем поговорим дальше?", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(F.text == "🤖 Gemini AI")
async def cmd_gemini_info(message: types.Message):
    await message.answer(
        "🤖 <b>Режим общения с Gemini AI активен.</b>\n\n"
        "Просто напишите мне любой вопрос, попросите написать код, текст, план или пришлите фото — я сразу отвечу!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.message(F.photo)
async def handle_photo(message: types.Message, bot: Bot):
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
    
    # 1. Check if user asks to draw / generate an image naturally
    draw_match = re.match(r"^(?:нарисуй|сгенерируй\s+картинку|сделай\s+картинку|нарисуй\s+мне|нарисуйте)\s+(.+)", text, re.IGNORECASE)
    if draw_match:
        prompt = draw_match.group(1).strip()
        status_msg = await message.answer("🎨 <i>Генерирую изображение через нейросеть Flux...</i>", parse_mode=ParseMode.HTML)
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        success, img_bytes, p_res = await generate_image_bytes(prompt)
        try:
            await status_msg.delete()
        except Exception:
            pass
        if success and img_bytes:
            photo_file = BufferedInputFile(img_bytes, filename="art.jpg")
            await message.answer_photo(photo_file, caption=f"✨ <b>{p_res}</b>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return
        else:
            await message.answer(f"❌ {p_res}", reply_markup=get_main_menu())
            return

    # 2. Check if user asks to set a reminder naturally
    if re.match(r"^(?:напомни|напомнить|поставь\s+напоминание|сделай\s+напоминание)\s+", text, re.IGNORECASE):
        raw = re.sub(r"^(?:напомни|напомнить|поставь\s+напоминание|сделай\s+напоминание)\s*", "", text, flags=re.IGNORECASE).strip()
        success, target_dt, task_text, info = await parse_natural_reminder(raw)
        if success and target_dt:
            item = add_reminder(message.from_user.id, task_text, target_dt)
            time_formatted = target_dt.strftime("%d.%m.%Y в %H:%M MSK")
            reply = (
                f"✅ <b>Напоминание установлено!</b>\n\n"
                f"📌 <b>Задача:</b> {task_text}\n"
                f"🕒 <b>Время:</b> {time_formatted}\n"
                f"<i>(ID: <code>{item['id']}</code>)</i>"
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
            return

    # 3. Default: General Gemini AI conversation
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ai_reply = await ask_gemini(message.from_user.id, text)
    
    try:
        await message.answer(ai_reply, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
    except Exception:
        await message.answer(ai_reply, reply_markup=get_main_menu())
