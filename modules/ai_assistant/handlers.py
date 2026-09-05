from aiogram.fsm.context import FSMContext
from typing import Dict, Any, Optional, List
import io
import html
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
from modules.gourmet_assistant.shelf_advisor import (
    analyze_alcohol_shelf,
    format_shelf_advisor_message,
    ask_shelf_followup,
    is_shelf_followup_question
)
from modules.gourmet_assistant.food_pairing import (
    is_food_pairing_query,
    get_food_pairing_recommendation
)
from modules.gourmet_assistant.storage import set_shelf_session, get_shelf_session

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
@router.message(F.text.in_(["🏁 Закончить режим (Главное меню)", "🏁 Закончить режим", "/stop", "/exit"]))
async def cmd_clear(message: types.Message, state: FSMContext):
    await state.clear()
    end_image_session(message.from_user.id)
    reset_chat_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    await message.answer("🏁 <b>Режим завершен.</b> Вы вернулись в главное меню!", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.message(F.text == "🤖 Gemini AI")
async def cmd_gemini_info(message: types.Message, state: FSMContext):
    await state.clear()
    from core.keyboards import get_mode_keyboard
    end_image_session(message.from_user.id)
    set_user_awaiting_image(message.from_user.id, False)
    await message.answer(
        "🤖 <b>Режим прямого диалога с Gemini AI:</b>\n\n"
        "Задавайте любые вопросы, просите написать код, составить план или проанализировать данные.\n"
        "<i>(Огромная панель кнопок скрыта для удобного чтения. Когда захотите выйти — нажмите кнопку завершения ниже)</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_mode_keyboard("Gemini AI")
    )


# --- MULTIMODAL PHOTO CLASSIFIER & ROUTER ---

# In-memory photo session storage: {user_id: {"image_bytes": bytes, "data": dict, "timestamp": float}}
_pending_photo_sessions: Dict[int, Dict[str, Any]] = {}


def set_pending_photo_session(user_id: int, image_bytes: bytes, data: dict):
    import time
    _pending_photo_sessions[user_id] = {
        "image_bytes": image_bytes,
        "data": data,
        "timestamp": time.time()
    }


def get_pending_photo_session(user_id: int) -> Optional[Dict[str, Any]]:
    import time
    sess = _pending_photo_sessions.get(user_id)
    if not sess:
        return None
    if time.time() - sess.get("timestamp", 0) > 3 * 3600:
        _pending_photo_sessions.pop(user_id, None)
        return None
    return sess


async def classify_photo_multimodal(image_bytes: bytes, caption: str = "") -> dict:
    """Умный классификатор: определяет категорию, точное название и КБЖУ в один вызов"""
    prompt = (
        "Ты — высокоточный мультимодальный классификатор для Telegram-бота.\n"
        "Внимательно изучи изображение и определи, что именно на нём изображено.\n\n"
        "1. main_category:\n"
        "   - 'alcohol_drink': если на фото бутылка или банка пива, вино, крепкий алкоголь, сидр, коктейль, винная полка в магазине или бар.\n"
        "   - 'food_dish': если на фото готовое блюдо на тарелке, фастфуд, пицца, салат, десерт, выпечка, суп, стейк.\n"
        "   - 'fridge_groceries': если на фото открытый холодильник или набор сырых продуктов для готовки.\n"
        "   - 'general': пейзаж, природа, машина, чек, код на экране, интерьер, документ, другое.\n"
        "2. title: Точное название конкретного объекта/напитка/блюда на русском (например: 'Пиво светлое Балтика №1', 'Вино Chianti Classico', 'Паста Карбонара', 'Стейк Рибай с овощами').\n"
        "3. drink_type: 'beer', 'wine', 'spirits', 'cocktail' или 'non_alcohol' (если это напиток).\n"
        "4. short_summary: Краткое (1 предложение) живое описание увиденного.\n"
        "5. food_kbju: расчет КБЖУ (dish_name, calories, protein, fat, carbs, estimated_weight_g, ingredients, healthy_verdict).\n\n"
        "Верни ТОЛЬКО валидный JSON в формате:\n"
        "{\n"
        '  "main_category": "alcohol_drink",\n'
        '  "title": "Пиво светлое Балтика №1",\n'
        '  "drink_type": "beer",\n'
        '  "short_summary": "Светлый лагер Балтика №1 в стеклянной бутылке на столе",\n'
        '  "food_kbju": {\n'
        '    "dish_name": "Пиво светлое Балтика №1",\n'
        '    "calories": 150,\n'
        '    "protein": 1.5,\n'
        '    "fat": 0.0,\n'
        '    "carbs": 14.0,\n'
        '    "estimated_weight_g": 450,\n'
        '    "ingredients": [{"name": "Пиво светлое", "weight": "450 мл", "kcal": 150, "p": 1.5, "f": 0.0, "c": 14.0}],\n'
        '    "healthy_verdict": "Светлое фильтрованное пиво"\n'
        '  }\n'
        "}"
    )
    try:
        resp = await ask_gemini(157236577, prompt, image_bytes=image_bytes)
        import json
        m = re.search(r"\{.*\}", resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        logger.warning(f"Error in classify_photo_multimodal: {e}")

    return {
        "main_category": "general",
        "title": "Объект на фото",
        "drink_type": "other",
        "short_summary": caption or "Фотография получена",
        "food_kbju": {}
    }


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

        # Умная мультимодальная классификация кадра
        classified = await classify_photo_multimodal(image_bytes, caption)
        cat = classified.get("main_category", "general")
        title = html.escape(str(classified.get("title", "Объект на фото")))
        summary = html.escape(str(classified.get("short_summary", "")))
        drink_type = classified.get("drink_type", "alcohol")
        
        # Сохраняем сессию фото в кэш
        set_pending_photo_session(user_id, image_bytes, classified)
        set_shelf_session(user_id, image_bytes, {"top_pick": {"name": title}})

        # 1. АЛКОГОЛЬ, ПИВО, ВИНО, ПОЛКА МАГАЗИНА (Сомелье в приоритете!)
        if cat == "alcohol_drink":
            is_beer = "пив" in title.lower() or drink_type == "beer" or "лагер" in title.lower() or "эль" in title.lower()
            icon = "🍺" if is_beer else "🍷"
            somm_label = "🍺 Пивной сомелье (Вкус & сорт)" if is_beer else "🍷 Винный сомелье (Разбор & вкус)"
            pair_label = "🥨 Закуски & Снеки к пиву" if is_beer else "🥩 Гастропара к напитку"
            
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=somm_label, callback_data="act_somm_eval"),
                        InlineKeyboardButton(text=pair_label, callback_data="act_somm_pair")
                    ],
                    [
                        InlineKeyboardButton(text="⭐ Рейтинг & Отзывы", callback_data="act_somm_rate"),
                        InlineKeyboardButton(text="🥗 Расчет КБЖУ и запись", callback_data="act_somm_kbju")
                    ],
                    [
                        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
                    ]
                ]
            )
            await message.answer(
                f"📸 <b>Распознано:</b> {icon} <b>{title}</b>\n"
                f"<i>«{summary}»</i>\n\n"
                f"👉 <b>Выберите, в каком формате разобрать этот напиток:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
            return

        # 2. ГОТОВОЕ БЛЮДО / ЕДА
        if cat == "food_dish":
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📊 Записать в дневник КБЖУ", callback_data="act_food_do_log"),
                        InlineKeyboardButton(text="🍳 Рецепт от Шеф-повара", callback_data="act_food_recipe")
                    ],
                    [
                        InlineKeyboardButton(text="🍷 Подобрать напиток/вино", callback_data="act_food_pairing"),
                        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
                    ]
                ]
            )
            await message.answer(
                f"📸 <b>Распознано блюдо:</b> 🥗 <b>{title}</b>\n"
                f"<i>«{summary}»</i>\n\n"
                f"👉 <b>Выберите интересующее действие:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
            return

        # 3. ХОЛОДИЛЬНИК / ИНГРЕДИЕНТЫ
        if cat == "fridge_groceries":
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="👨‍🍳 Шедевр Шефа из наличия", callback_data="act_fridge_chef"),
                        InlineKeyboardButton(text="🥗 Расчет КБЖУ продуктов", callback_data="act_food_do_log")
                    ],
                    [
                        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
                    ]
                ]
            )
            await message.answer(
                f"📸 <b>Распознаны продукты:</b> 🍳 <b>{title}</b>\n"
                f"<i>«{summary}»</i>\n\n"
                f"👉 <b>Что приготовим?</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
            return

        # 4. ОБЩИЙ РЕЖИМ (Пейзаж, код, чек, предмет)
        prompt_text = caption or "Подробно и полезно ответь на вопрос пользователя или опиши изображение."
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

    # 0. Interactive Quick Topic Router (Выходные, Отдых, Загород, Сомелье, Бармен, Кино, Ужин)
    if t_lower in ["выходные", "выходной", "уикенд", "отдых", "загород", "куда сходить", "что поделать", "планы на выходные", "куда поехать"]:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏕 Загородные клубы, Бани & Спа", callback_data="act_goto_country"),
                ],
                [
                    InlineKeyboardButton(text="🚗 Авто-маршруты & Роадтрипы", callback_data="act_goto_weekend"),
                ],
                [
                    InlineKeyboardButton(text="👶 Отдых с малышом (1–3 года)", callback_data="act_goto_kids"),
                ],
                [
                    InlineKeyboardButton(text="🎬 Киномарафон & Фильмы", callback_data="act_goto_cinema"),
                    InlineKeyboardButton(text="🍳 Рецепты от Шефа", callback_data="act_goto_chef")
                ],
                [
                    InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
                ]
            ]
        )
        await message.answer(
            "✨ <b>Интерактивный подбор планов на выходные:</b>\n\n"
            "Я могу составить идеальный сценарий отдыха! Выберите подходящее направление:",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
        return

    if t_lower in ["сомелье", "вино", "выбрать вино", "алкоголь", "бармен", "коктейль", "коктейли", "пиво"]:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🍷 Винный гид & Подбор по полке", callback_data="act_goto_sommelier"),
                ],
                [
                    InlineKeyboardButton(text="🥩 Гастропара (Вино под блюдо)", callback_data="act_goto_pairing"),
                ],
                [
                    InlineKeyboardButton(text="🍸 Авторские коктейли & Бармен", callback_data="act_goto_cocktails"),
                ],
                [
                    InlineKeyboardButton(text="📚 Книжный сомелье", callback_data="act_goto_book_sommelier"),
                    InlineKeyboardButton(text="🎵 Музыкальный сомелье", callback_data="act_goto_music_sommelier")
                ],
                [
                    InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
                ]
            ]
        )
        await message.answer(
            "🍷 <b>Интерактивный Сомелье & Бармен гид:</b>\n\n"
            "Выберите интересующий модуль или просто отправьте фото полки в магазине / блюда:",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
        return

    # Check if user is asking for Food Pairing ("буду кушать пиццу, какое пиво взять?", "под стейк какое вино?", etc.)
    if is_food_pairing_query(text):
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        shelf_sess = get_shelf_session(user_id)
        pairing_ans = await get_food_pairing_recommendation(
            user_id=user_id,
            query=text,
            active_shelf_data=shelf_sess.get("shelf_data") if shelf_sess else None,
            image_bytes=shelf_sess.get("image_bytes") if shelf_sess else None
        )
        try:
            await message.answer(pairing_ans, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        except Exception:
            await message.answer(pairing_ans, reply_markup=get_main_menu())
        return

    # Check if user is asking an interactive follow-up about a recently scanned shelf
    shelf_sess = get_shelf_session(user_id)
    if shelf_sess and is_shelf_followup_question(text):
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        resp = await ask_shelf_followup(
            user_id=user_id,
            question=text,
            shelf_data=shelf_sess.get("shelf_data", {}),
            image_bytes=shelf_sess.get("image_bytes")
        )
        try:
            await message.answer(resp, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        except Exception:
            await message.answer(resp, reply_markup=get_main_menu())
        return

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

    # 5. New Features Menu Buttons & Quick Triggers
    if text == "🍳 Завтрак & 🍸 Бармен":
        from modules.gourmet_assistant.handlers import cmd_breakfast
        await cmd_breakfast(message)
        return

    if text == "🎁 Промокоды & 🎮 Игры":
        from modules.freebies_promos.handlers import cmd_promos
        await cmd_promos(message)
        return

    if text == "🚗 Авто-Юрист & 🚨 ДТП":
        from modules.auto_legal_aid.handlers import cmd_dtp
        await cmd_dtp(message)
        return

    if text == "🔬 Deep Research & 🛡 Фактчек":
        from modules.ai_deep_research.handlers import cmd_research
        await cmd_research(message)
        return

    if text == "📵 Проверить номер":
        await message.answer(
            "📵 <b>Антиспам-чекер номеров:</b>\n\n"
            "Отправьте номер телефона в чат для проверки репутации и оператора:\n"
            "👉 <code>+7 (921) 123-45-67</code>\n"
            "👉 <i>«Чей номер +78124567890?»</i>\n"
            "👉 <i>«Кто звонил 89001112233?»</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
        return

    # Anti-Spam Phone Detection (if user sends phone number or asks 'кто звонил')
    phone_match = re.search(r"(?:\+7|8)[\s\-(]?\d{3}[\s\-)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", text)
    if phone_match and any(k in t_lower for k in ["номер", "звонил", "кто", "спам", "проверь", "чей", "откуда", "+7", "89", "8812"]):
        from modules.anti_spam_guard.checker import check_phone_number_reputation
        from modules.anti_spam_guard.handlers import format_spam_card
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        data = await check_phone_number_reputation(user_id, phone_match.group(0))
        await message.answer(format_spam_card(data), parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
        return

    # 5.1 Birthday Natural Language Add/Delete Triggers (Direct Cloud-Synced DB execution)
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


# --- INTERACTIVE MODULE ROUTER CALLBACKS ---

@router.callback_query(F.data == "act_shelf_sommelier")
async def cb_shelf_sommelier(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    shelf_sess = get_shelf_session(user_id)
    if not shelf_sess:
        await callback.answer("⚠️ Срок сессии фото истек. Отправьте фото заново.", show_alert=True)
        return
    await callback.answer("🍷 Анализирую полку как сомелье...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    question = "Выдели 2-3 самых лучших вина на этой полке по соотношению цена/качество. Объясни сорта винограда, вкусовой профиль и почему их стоит взять."
    resp = await ask_shelf_followup(
        user_id=user_id,
        question=question,
        shelf_data=shelf_sess.get("shelf_data", {}),
        image_bytes=shelf_sess.get("image_bytes")
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🥩 Гастропара к блюдам", callback_data="act_shelf_pairing"),
                InlineKeyboardButton(text="⭐ Vivino & Рейтинги", callback_data="act_shelf_ratings")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "act_shelf_pairing")
async def cb_shelf_pairing(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    shelf_sess = get_shelf_session(user_id)
    if not shelf_sess:
        await callback.answer("⚠️ Отправьте фото полки заново.", show_alert=True)
        return
    await callback.answer("🥩 Подбираю гастрономические пары...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    question = "Подбери идеальные гастропары (food pairing) к винам/напиткам на этом фото: что взять под стейк/мясо, что под морепродукты/рыбу, и что под сырную тарелку."
    resp = await ask_shelf_followup(
        user_id=user_id,
        question=question,
        shelf_data=shelf_sess.get("shelf_data", {}),
        image_bytes=shelf_sess.get("image_bytes")
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍷 Топ сомелье", callback_data="act_shelf_sommelier"),
                InlineKeyboardButton(text="⭐ Рейтинги Vivino", callback_data="act_shelf_ratings")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "act_shelf_ratings")
async def cb_shelf_ratings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    shelf_sess = get_shelf_session(user_id)
    if not shelf_sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
    await callback.answer("⭐ Оцениваю рейтинги и выгоду...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    question = "Оцени рейтинг вин на фото по шкале Vivino и мировым винным критикам. Укажи, какие позиции сейчас продаются по честной и выгодной цене, а какие переоценены."
    resp = await ask_shelf_followup(
        user_id=user_id,
        question=question,
        shelf_data=shelf_sess.get("shelf_data", {}),
        image_bytes=shelf_sess.get("image_bytes")
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍷 Топ сомелье", callback_data="act_shelf_sommelier"),
                InlineKeyboardButton(text="🥩 Гастропара", callback_data="act_shelf_pairing")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "act_shelf_cocktails")
async def cb_shelf_cocktails(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    shelf_sess = get_shelf_session(user_id)
    if not shelf_sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
    await callback.answer("🍸 Составляю рецепты коктейлей...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    question = "Предложи 2-3 авторских или классических коктейля, которые можно приготовить с напитками с этой полки, с рецептом и пропорциями."
    resp = await ask_shelf_followup(
        user_id=user_id,
        question=question,
        shelf_data=shelf_sess.get("shelf_data", {}),
        image_bytes=shelf_sess.get("image_bytes")
    )
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


# Быстрые переходы в модули
@router.callback_query(F.data == "act_goto_country")
async def cb_goto_country(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🏕 Перехожу в модуль Загородный отдых...")
    from modules.country_relax.handlers import cmd_country_relax
    await cmd_country_relax(callback.message, state)


@router.callback_query(F.data == "act_goto_weekend")
async def cb_goto_weekend(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🚗 Перехожу в модуль Сценарист выходных...")
    from modules.weekend_trips.handlers import cmd_weekend_trips
    await cmd_weekend_trips(callback.message, state)


@router.callback_query(F.data == "act_goto_kids")
async def cb_goto_kids(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("👶 Открываю развлечения для малыша 1–3 года...")
    from core.states import ActiveModeStates
    from modules.weekend_trips.handlers import get_kids_menu_keyboard
    await state.set_state(ActiveModeStates.weekend_planner_mode)
    text = (
        "👶 <b>Развлечения с малышом 1–3 года в Санкт-Петербурге и ЛО:</b>\n\n"
        "Мягкие тоддлер-зоны 0–3, камерные бэби-театры на подушках, тёплые лягушатники (+32...+34°C), "
        "пушистые ручные альпаки, океанариум и живописные экотропы под детскую коляску!\n\n"
        "👇 <b>Выберите категорию для малыша:</b>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_kids_menu_keyboard())


@router.callback_query(F.data == "act_goto_cinema")
async def cb_goto_cinema(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🎬 Перехожу в Киносомелье...")
    from modules.cinema_matchmaker.handlers import cmd_cinema_matchmaker
    await cmd_cinema_matchmaker(callback.message, state)


@router.callback_query(F.data == "act_goto_chef")
async def cb_goto_chef(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🍳 Перехожу в Шеф-повар из холодильника...")
    from modules.dark_kitchen.handlers import cmd_dark_kitchen
    await cmd_dark_kitchen(callback.message, state)


@router.callback_query(F.data == "act_goto_sommelier")
async def cb_goto_sommelier(callback: types.CallbackQuery):
    await callback.answer("🍷 Модуль Винный сомелье активирован!")
    await callback.message.answer(
        "🍷 <b>Винный сомелье & Кавист:</b>\n\n"
        "📸 <b>Просто отправьте фото полки в супермаркете или винотеке</b> — я моментально определю сорта, лучшие винтажи, соотношение цена/качество и скидки!\n\n"
        "💬 <i>Либо напишите, какое вино ищете: «Красное сухое до 1500 рублей под мясо».</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "act_goto_pairing")
async def cb_goto_pairing(callback: types.CallbackQuery):
    await callback.answer("🥩 Модуль Гастропара активирован!")
    await callback.message.answer(
        "🥩 <b>Гастрономический гид (Food Pairing):</b>\n\n"
        "Напишите, какое блюдо вы планируете приготовить или заказать (например: <i>«Стейк рибай прожарки medium», «Паста с морепродуктами», «Утка с яблоками»</i>) — и я подберу идеальный напиток!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "act_goto_cocktails")
async def cb_goto_cocktails(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🍸 Модуль Бармен активирован!")
    from modules.gourmet_assistant.handlers import cmd_cocktails
    await cmd_cocktails(callback.message, state)


@router.callback_query(F.data == "act_goto_book_sommelier")
async def cb_goto_book_sommelier(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("📚 Модуль Книжный сомелье...")
    from modules.book_sommelier.handlers import cmd_book_sommelier
    await cmd_book_sommelier(callback.message, state)


@router.callback_query(F.data == "act_goto_music_sommelier")
async def cb_goto_music_sommelier(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🎵 Модуль Музыкальный сомелье...")
    from modules.music_sommelier.handlers import cmd_music_sommelier
    await cmd_music_sommelier(callback.message, state)


# --- DEDICATED SOMMELIER & FOOD INTERACTIVE CALLBACKS ---

@router.callback_query(F.data == "act_somm_eval")
async def cb_somm_eval(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Сессия фото истекла. Отправьте фото заново.", show_alert=True)
        return
    
    data = sess.get("data", {})
    title = data.get("title", "Напиток")
    img = sess.get("image_bytes")
    
    await callback.answer("🍺 Составляю разбор сомелье...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    prompt = (
        f"Ты — признанный пивной и винный сомелье (кавист).\n"
        f"Внимательно изучи напиток на фото (название: «{title}»).\n\n"
        "Составь профессиональный и сочный разбор сомелье:\n"
        "1. 🍺/🍷 **СТИЛЬ И ХАРАКТЕР:** Стиль/сорт (светлый лагер, пилснер, IPA, стаут, сухое вино), плотность, цвет, карбонизация, крепость.\n"
        "2. 👃 **АРОМАТ И ВКУСОВЫЕ НОТЫ:** Баланс солодовой сладости, хмелевая горечь (IBU), освежающий профиль, послевкусие.\n"
        "3. ❄️ **ИДЕАЛЬНАЯ ПОДАЧА:** Температура сервировки (°C), рекомендуемая форма бокала (пилснер, тюльпан, пинта).\n"
        "4. 🎯 **ВЕРДИКТ СОМЕЛЬЕ:** Честная экспертная оценка, для каких ситуаций подходит лучше всего.\n\n"
        "Форматируй ответ в красивом HTML (<b>, <i>, <code>), используй живые эмодзи."
    )
    
    resp = await ask_gemini(user_id, prompt, image_bytes=img)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🥨 Закуски & Снеки к напитку", callback_data="act_somm_pair"),
                InlineKeyboardButton(text="⭐ Рейтинг & Отзывы", callback_data="act_somm_rate")
            ],
            [
                InlineKeyboardButton(text="🥗 Расчет КБЖУ и запись в рацион", callback_data="act_somm_kbju"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    
    try:
        await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        await callback.message.reply(resp, reply_markup=kb)


@router.callback_query(F.data == "act_somm_pair")
async def cb_somm_pair(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
        
    data = sess.get("data", {})
    title = data.get("title", "Напиток")
    img = sess.get("image_bytes")
    
    await callback.answer("🥨 Подбираю идеальные закуски...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    prompt = (
        f"Ты — шеф-повар и эксперт по гастропарам (food pairing).\n"
        f"Подбери лучшие закуски, снеки и блюда, которые идеально раскроют вкус напитка «{title}»:\n\n"
        "1. 🍟 **Быстрые снеки к бокалу:** (чипсы, гренки, сыр, орешки, вяленая рыба/мясо)\n"
        "2. 🍤 **Горячие закуски:** (крылышки, креветки, колбаски, кольца кальмара, жареный сыр)\n"
        "3. 🍕 **Сытные блюда:** (пицца, бургеры, стейк, шашлык)\n"
        "4. 💡 **Необычный совет от шефа:** секретный вкусовой акцент.\n\n"
        "Форматируй в HTML с эмодзи."
    )
    
    resp = await ask_gemini(user_id, prompt, image_bytes=img)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍺 Разбор вкуса сомелье", callback_data="act_somm_eval"),
                InlineKeyboardButton(text="⭐ Рейтинг & Отзывы", callback_data="act_somm_rate")
            ],
            [
                InlineKeyboardButton(text="🥗 Записать в КБЖУ", callback_data="act_somm_kbju"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    
    try:
        await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        await callback.message.reply(resp, reply_markup=kb)


@router.callback_query(F.data == "act_somm_rate")
async def cb_somm_rate(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
        
    data = sess.get("data", {})
    title = data.get("title", "Напиток")
    img = sess.get("image_bytes")
    
    await callback.answer("⭐ Анализирую рейтинги и репутацию...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    prompt = (
        f"Расскажи о репутации, оценках и отзывах о напитке «{title}»:\n"
        "1. ⭐️ **Рейтинг ценителей:** (Untappd / RateBeer / Vivino / Киноманы / Отзовик).\n"
        "2. 🏭 **Производитель и история:** Где и кем производится, традиции завода.\n"
        "3. 💰 **Честность цены:** Оправдана ли стоимость на полке, есть ли более интересные аналоги за те же деньги.\n\n"
        "Форматируй в HTML с эмодзи."
    )
    
    resp = await ask_gemini(user_id, prompt, image_bytes=img)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍺 Разбор сомелье", callback_data="act_somm_eval"),
                InlineKeyboardButton(text="🥨 Закуски & Снеки", callback_data="act_somm_pair")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    try:
        await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        await callback.message.reply(resp, reply_markup=kb)


@router.callback_query(F.data.in_(["act_somm_kbju", "act_food_do_log"]))
async def cb_food_log(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Срок сессии истек. Отправьте фото заново.", show_alert=True)
        return
        
    data = sess.get("data", {})
    food = data.get("food_kbju", {})
    title = food.get("dish_name") or data.get("title", "Блюдо")
    kcal = food.get("calories", 150)
    p = food.get("protein", 1.5)
    f = food.get("fat", 0.0)
    c = food.get("carbs", 14.0)
    weight = food.get("estimated_weight_g", 450)
    ingredients = food.get("ingredients", [])
    verdict = food.get("healthy_verdict", "")

    breakdown_lines = []
    for ing in ingredients[:5]:
        breakdown_lines.append(f"• {ing.get('name')} ({ing.get('weight', '')}): {ing.get('kcal', '')} ккал (Б:{ing.get('p')} Ж:{ing.get('f')} У:{ing.get('c')})")
    breakdown_str = "\n".join(breakdown_lines)

    entry = log_meal(user_id, title, kcal, p, f, c, weight_g=weight, breakdown_text=breakdown_str)
    summary = get_daily_summary(user_id)

    weight_info = f"⚖️ <i>Примерный вес: ~{weight} г</i>\n" if weight else ""
    ing_info = f"📋 <b>Состав:</b>\n{breakdown_str}\n\n" if breakdown_str else ""
    verdict_info = f"💡 <i>{verdict}</i>\n\n" if verdict else ""

    card_text = (
        f"✅ <b>Записано в дневник питания!</b>\n\n"
        f"🥗 <b>{title}</b>\n"
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

    await callback.answer("✅ Успешно записано в рацион!")
    await callback.message.reply(card_text, parse_mode=ParseMode.HTML, reply_markup=get_food_meal_keyboard(entry["id"]))


@router.callback_query(F.data == "act_food_recipe")
async def cb_food_recipe(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
        
    title = sess.get("data", {}).get("title", "Блюдо")
    img = sess.get("image_bytes")
    
    await callback.answer("🍳 Составляю авторский рецепт...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    prompt = (
        f"Ты — шеф-повар ресторана. Составь идеальный авторский рецепт приготовления блюда «{title}»:\n"
        "1. 🛒 Список ингредиентов и точные пропорции.\n"
        "2. 👨‍🍳 Пошаговый процесс приготовления (температура, время, текстура).\n"
        "3. 🌟 Секретный соус или фишка от шефа, делающая вкус незабываемым.\n\n"
        "Форматируй в HTML с эмодзи."
    )
    resp = await ask_gemini(user_id, prompt, image_bytes=img)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍷 Подобрать напиток к блюду", callback_data="act_food_pairing"),
                InlineKeyboardButton(text="📊 Записать в КБЖУ", callback_data="act_food_do_log")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(F.data == "act_food_pairing")
async def cb_food_pairing_btn(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
        
    title = sess.get("data", {}).get("title", "Блюдо")
    img = sess.get("image_bytes")
    
    await callback.answer("🍷 Подбираю напитки к блюду...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    prompt = (
        f"Ты — сомелье по ресторанному фудпейрингу. Подбери 3 идеальных напитка под блюдо «{title}»:\n"
        "1. 🍷 Идеальное вино (сорт, регион, почему подходит)\n"
        "2. 🍺 Идеальное пиво или сидр (стиль, горечь/сладость)\n"
        "3. 🍹 Безалкогольная пара (авторский лимонад / чай / моктейль)\n\n"
        "Форматируй в HTML."
    )
    resp = await ask_gemini(user_id, prompt, image_bytes=img)
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.callback_query(F.data == "act_fridge_chef")
async def cb_fridge_chef(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    sess = get_pending_photo_session(user_id)
    if not sess:
        await callback.answer("⚠️ Отправьте фото заново.", show_alert=True)
        return
        
    title = sess.get("data", {}).get("title", "Продукты")
    img = sess.get("image_bytes")
    
    await callback.answer("👨‍🍳 Готовлю рецепт из наличия...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    prompt = (
        f"Ты — шеф-повар Dark Kitchen. Посмотри на продукты на фото ({title}) и придумай "
        "ресторанный ужин за 15 минут строго из того, что есть на фото, с пошаговыми инструкциями!"
    )
    resp = await ask_gemini(user_id, prompt, image_bytes=img)
    await callback.message.reply(resp, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


