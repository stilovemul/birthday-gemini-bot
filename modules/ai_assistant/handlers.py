import io
import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import CommandStart, Command
from core.keyboards import get_main_menu
from core.gemini import ask_gemini, reset_chat_session

logger = logging.getLogger("AIAssistantHandler")
router = Router(name="ai_assistant")


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 <b>Привет, Олег! Модульный бот AiGemAntigravity активен 24/7!</b> 🚀\n\n"
        "Я твой персональный облачный помощник, объединяющий возможности <b>Google Gemini AI</b>, "
        "напоминания о днях рождения, быстрые заметки и другие модули.\n\n"
        "💬 <b>Основные разделы:</b>\n"
        "• 🤖 <b>Gemini AI</b>: пиши любые вопросы, общайся, советуйся или присылай фото\n"
        "• 🎂 <b>Дни рождения</b>: меню внизу или <code>/add Имя Дата [Заметка]</code>\n"
        "• 📝 <b>Заметки</b>: сохраняй мысли командой <code>/note Текст</code>\n"
        "• <code>/clear</code> — сбросить контекст диалога с ИИ\n\n"
        "Выберите раздел меню или просто напишите мне сообщение 👇"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(Command("help"))
@router.message(F.text == "❓ Справка")
async def cmd_help(message: types.Message):
    help_text = (
        "📖 <b>Справка по возможностям бота:</b>\n\n"
        "🤖 <b>Gemini AI:</b>\n"
        "Пишите любой текст или отправляйте фото для анализа.\n"
        "• <code>/clear</code> — начать новую тему разговора\n\n"
        "🎂 <b>Дни рождения:</b>\n"
        "• <code>/add Мама 06.04.1964 Цветы</code>\n"
        "• <code>/list</code> — все дни рождения\n"
        "• <code>/upcoming</code> — праздники на 30 дней\n"
        "• <code>/today</code> — именинники сегодня\n"
        "• <code>/del Имя_или_ID</code> — удалить запись\n\n"
        "📝 <b>Быстрые заметки:</b>\n"
        "• <code>/note Купить подарок</code> — добавить заметку\n"
        "• <code>/notes</code> — список заметок\n"
        "• <code>/delnote ID</code> — удалить заметку"
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
        "Просто напишите мне любой вопрос, попросите написать код, текст, составить план или пришлите фото — я сразу отвечу!",
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
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    ai_reply = await ask_gemini(message.from_user.id, text)
    try:
        await message.answer(ai_reply, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_menu())
    except Exception:
        await message.answer(ai_reply, reply_markup=get_main_menu())
