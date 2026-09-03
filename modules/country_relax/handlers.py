import html
import logging
import urllib.parse
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.country_relax.finder import find_country_resorts
from modules.country_relax.storage import (
    get_user_last_country,
    save_last_country_resort,
    get_last_country_resort
)
from modules.country_relax.advisor import process_country_conversation
from modules.voice_assistant.transcriber import transcribe_audio_gemini

logger = logging.getLogger("CountryRelaxHandlers")
router = Router(name="country_relax")


def get_country_qa_keyboard(category: str = "general", geo_query: str = "") -> InlineKeyboardMarkup:
    """Клавиатура под ответом консьержа для продолжения диалога или быстрого перехода."""
    rows = [
        [
            InlineKeyboardButton(text="🔄 Другой вариант (Ещё)", callback_data=f"cr_more_{category}")
        ],
        [
            InlineKeyboardButton(text="👨‍👩‍👧 С детьми", callback_data="cr_preset_family"),
            InlineKeyboardButton(text="🏊‍♂️ Бассейны & Спа", callback_data="cr_preset_pool")
        ]
    ]
    if geo_query:
        encoded = urllib.parse.quote(geo_query)
        maps_url = f"https://yandex.ru/maps/?text={encoded}"
        rows.append([
            InlineKeyboardButton(text="🗺 Найти на Яндекс.Картах", url=maps_url)
        ])
    rows.append([
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)



def get_country_start_keyboard() -> InlineKeyboardMarkup:
    """Стартовая клавиатура быстрого выбора загородного отдыха."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍👩‍👧 Семейные курорты & С детьми", callback_data="cr_preset_family"),
                InlineKeyboardButton(text="🏊‍♂️ Теплые бассейны & Спа", callback_data="cr_preset_pool")
            ],
            [
                InlineKeyboardButton(text="🪵 Русская баня & Чан у воды", callback_data="cr_preset_banya"),
                InlineKeyboardButton(text="🏕 Стильный глэмпинг в лесу", callback_data="cr_preset_glamp")
            ],
            [
                InlineKeyboardButton(text="🎣 Коттеджи у озера & Рыбалка", callback_data="cr_preset_lake"),
                InlineKeyboardButton(text="💎 Романтик & Премиум", callback_data="cr_preset_romantic")
            ],
            [
                InlineKeyboardButton(text="🎲 Топ-локация для всей семьи", callback_data="cr_preset_random")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_country_card_keyboard(category: str, geo_query: str = "") -> InlineKeyboardMarkup:
    """Клавиатура под карточкой базы отдыха: кнопка «Другой вариант» на первом месте."""
    rows = [
        [
            InlineKeyboardButton(text="🔄 Другой вариант (Ещё)", callback_data=f"cr_more_{category}")
        ],
        [
            InlineKeyboardButton(text="👨‍👩‍👧 С детьми", callback_data="cr_preset_family"),
            InlineKeyboardButton(text="🏊‍♂️ Бассейны & Спа", callback_data="cr_preset_pool")
        ],
        [
            InlineKeyboardButton(text="🪵 Бани & Чан", callback_data="cr_preset_banya"),
            InlineKeyboardButton(text="🏕 Глэмпинги", callback_data="cr_preset_glamp")
        ],
        [
            InlineKeyboardButton(text="🎣 Озеро & Рыбалка", callback_data="cr_preset_lake"),
            InlineKeyboardButton(text="💎 Романтик", callback_data="cr_preset_romantic")
        ]
    ]

    if geo_query:
        encoded = urllib.parse.quote(geo_query)
        maps_url = f"https://yandex.ru/maps/?text={encoded}"
        rows.append([
            InlineKeyboardButton(text="🗺 Найти на Яндекс.Картах", url=maps_url)
        ])

    rows.append([
        InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


COUNTRY_ENTRY_PHRASES = {
    "🏕 загород",
    "загород",
    "🏕 загородный отдых",
    "загородный отдых",
    "загородный семейный отдых",
    "семейный загородный отдых",
    "семейный отдых",
    "отдых с детьми",
    "бани & спа",
    "бани и спа",
    "загородные клубы",
    "загородные отели"
}


def is_country_entry_command(text: str) -> bool:
    if not text:
        return False
    cleaned = text.replace("\ufe0f", "").strip().lower()
    return cleaned in COUNTRY_ENTRY_PHRASES


@router.message(Command("countryside"))
@router.message(Command("spa"))
@router.message(Command("banya"))
@router.message(Command("glamping"))
@router.message(Command("resort"))
@router.message(Command("relax"))
@router.message(F.text.func(is_country_entry_command))
async def cmd_country_relax(message: types.Message, state: FSMContext):
    """Точка входа в модуль «Загородный семейный отдых»."""
    await state.set_state(ActiveModeStates.country_relax_mode)
    welcome_text = (
        "🏕 <b>Загородный семейный отдых, Спа & Курорты:</b>\n\n"
        "Персональный консьерж по лучшим семейным загородным клубам, курортам для отдыха с детьми, спа-отелям с открытыми подогреваемыми бассейнами, коттеджам и баням СПб, Ленобласти и Карелии!\n\n"
        "💡 <b>Как подобрать идеальное место для семьи:</b>\n"
        "• Выберите категорию готовых курортов кнопками ниже 👇\n"
        "• Либо напишите ваш запрос в свободной форме:\n"
        "  - <i>«Коттедж для семьи с детьми 4 и 7 лет, детская площадка, озеро, до 1 часа от СПб»</i>\n"
        "  - <i>«Загородный клуб с открытым теплым бассейном и спа на выходные»</i>\n"
        "  - <i>«Семейная база с фермой кроликов, анимацией и прокатом велосипедов»</i>\n"
        "  - <i>«Уютный домик в сосновом бору с баней на дровах и рыбалкой»</i>\n\n"
        "💬 <i>Выберите категорию или напишите ваши пожелания текстом:</i>"
    )
    await message.answer(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_mode_keyboard("Загородный отдых")
    )
    await message.answer(
        "👇 <b>Быстрый подбор по категориям:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_country_start_keyboard()
    )


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_country(callback: types.CallbackQuery, state: FSMContext):
    """Выход из режима «Загородный отдых» в главное меню."""
    await state.clear()
    await callback.answer("Вы вышли в главное меню")
    await callback.message.answer(
        "🏁 <b>Режим «Загородный отдых» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data.startswith("cr_preset_"))
async def cb_country_preset(callback: types.CallbackQuery, state: FSMContext):
    """Обработка готовых категорий загородного отдыха."""
    category = callback.data.replace("cr_preset_", "").strip()
    await state.set_state(ActiveModeStates.country_relax_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    cat_titles = {
        "family": "👨‍👩‍👧 Семейные курорты & С детьми",
        "pool": "🏊‍♂️ Спа & Теплые бассейны",
        "banya": "🪵 Русские бани на дровах & Чан",
        "glamp": "🏕 Стильные глэмпинги в лесу",
        "lake": "🎣 Озеро & Рыбалка",
        "romantic": "💎 Романтик & Премиум",
        "random": "🎲 Топ-локация для всей семьи"
    }
    title = cat_titles.get(category, "Загородный отдых")
    await callback.answer(f"🔎 Подбираю: {title}...")

    queries = {
        "family": "Семейные загородные клубы, курорты и базы отдыха Ленинградской области с развитой детской инфраструктурой, игровыми городками, мини-зоопарками, прокатом и детским меню",
        "pool": "Загородные отели Ленобласти с открытым подогреваемым бассейном круглый год и спа-зоной для отдыха всей семьей",
        "banya": "Загородные базы отдыха на берегу озера с настоящей русской баней на дровах, купелью и чаном для семейного отдыха",
        "glamp": "Стильные глэмпинги, А-фреймы и купольные домики в сосновом лесу у воды с удобствами для семей",
        "lake": "Коттеджи на берегу озера или залива с лодками, рыбалкой, песчаным берегом и мангальной зоной",
        "romantic": "Премиальные загородные бутик-отели для романтического уикенда вдвоем",
        "random": "Лучший проверенный вариант загородного семейного отдыха в Ленинградской области прямо сейчас"
    }
    q = queries.get(category, "Семейный загородный отдых в Ленинградской области")
    res = await find_country_resorts(callback.from_user.id, q, category=category, is_another=False)
    await render_country_card(callback.message, res, category=category)


@router.callback_query(F.data.startswith("cr_more"))
async def cb_country_more(callback: types.CallbackQuery, state: FSMContext):
    """Подбор другого варианта (кнопка «Ещё» без повторов)."""
    raw_cat = callback.data.replace("cr_more_", "").replace("cr_more", "").strip("_")
    category = raw_cat if raw_cat else "general"

    await state.set_state(ActiveModeStates.country_relax_mode)
    await callback.answer("🔄 Подбираю другой проверенный вариант...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    last_info = get_user_last_country(callback.from_user.id)
    query = last_info.get("query") or "Другая отличная загородная база отдыха"
    res = await find_country_resorts(callback.from_user.id, query, category=category, is_another=True)
    await render_country_card(callback.message, res, category=category)


@router.message(ActiveModeStates.country_relax_mode, F.text)
async def handle_country_text(message: types.Message, state: FSMContext):
    """Обработка свободного текстового запроса или триггеров «еще»."""
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Загородный отдых» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    # Проверка триггеров «еще» / «другой вариант»
    t_lower = raw_text.lower()
    more_triggers = ["еще", "ещё", "другой", "другая", "другое", "дальше", "следующий", "вариант", "еще вариант", "ещё вариант"]
    if t_lower in more_triggers:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        last_info = get_user_last_country(message.from_user.id)
        query = last_info.get("query") or "Другой отличный загородный отель или база отдыха"
        cat = last_info.get("category") or "general"
        res = await find_country_resorts(message.from_user.id, query, category=cat, is_another=True)
        await render_country_card(message, res, category=cat)
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    # 1. Проверяем, задает ли пользователь вопрос по текущей базе отдыха (интерактивный диалог с консьержем)
    is_followup, ans_or_query = await process_country_conversation(message.from_user.id, raw_text)
    if is_followup and ans_or_query:
        last_r = get_last_country_resort(message.from_user.id) or {}
        geo_q = last_r.get("geo_query", "")
        await message.answer(
            ans_or_query,
            parse_mode=ParseMode.HTML,
            reply_markup=get_country_qa_keyboard(geo_query=geo_q)
        )
        return

    # 2. Иначе это новый поисковый запрос пользователя
    query_to_search = ans_or_query or raw_text
    res = await find_country_resorts(message.from_user.id, query_to_search, category="custom", is_another=False)
    await render_country_card(message, res, category="custom")


@router.message(ActiveModeStates.country_relax_mode, F.voice | F.video_note | F.audio)
async def handle_country_voice(message: types.Message, state: FSMContext):
    """Обработка голосовых вопросов и запросов в режиме Загородного отдыха."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    audio_obj = message.voice or message.video_note or message.audio
    try:
        file = await message.bot.get_file(audio_obj.file_id)
        file_bytes_io = await message.bot.download_file(file.file_path)
        audio_bytes = file_bytes_io.read()
    except Exception as e:
        logger.warning(f"Error downloading country voice: {e}")
        await message.answer("⚠️ Не удалось загрузить аудиосообщение. Напишите текстом.")
        return

    transcribed = await transcribe_audio_gemini(audio_bytes)
    if not transcribed:
        await message.answer("🎙 Не удалось расслышать голосовое сообщение. Попробуйте повторить или написать текстом.")
        return

    await message.answer(f"🎙 <b>Вы спросили:</b> <i>«{html.escape(transcribed)}»</i>", parse_mode=ParseMode.HTML)

    is_followup, ans_or_query = await process_country_conversation(message.from_user.id, transcribed)
    if is_followup and ans_or_query:
        last_r = get_last_country_resort(message.from_user.id) or {}
        geo_q = last_r.get("geo_query", "")
        await message.answer(
            ans_or_query,
            parse_mode=ParseMode.HTML,
            reply_markup=get_country_qa_keyboard(geo_query=geo_q)
        )
        return

    query_to_search = ans_or_query or transcribed
    res = await find_country_resorts(message.from_user.id, query_to_search, category="custom", is_another=False)
    await render_country_card(message, res, category="custom")


async def render_country_card(message: types.Message, resort: dict, category: str = "general"):
    """Форматирование и отправка стильной карточки загородного отдыха."""
    name = html.escape(str(resort.get("name", "Загородный клуб")))
    cat_title = html.escape(str(resort.get("category", "🏕 Загородный отдых")))
    location = html.escape(str(resort.get("location", "Ленинградская область")))
    price = html.escape(str(resort.get("price_range", "По запросу")))
    features = html.escape(str(resort.get("features", "Баня, спа, природа")))
    kid_friendly = html.escape(str(resort.get("kid_friendly", "Подходит для семей")))
    why_best = html.escape(str(resort.get("why_best", "Прекрасное место для отдыха на природе.")))
    tip = html.escape(str(resort.get("booking_tip", "Бронируйте заранее на официальном сайте.")))
    geo_query = resort.get("geo_query", name)

    # Сохраняем карточку в память для интерактивного диалога с вопросами
    save_last_country_resort(message.chat.id, resort)

    card_text = (
        f"🏕 <b>{name.upper()}</b>\n"
        f"<i>{cat_title}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📍 <b>Локация & Дорога:</b>\n{location}\n\n"
        f"💰 <b>Стоимость:</b>\n{price}\n\n"
        f"🪵 <b>Инфраструктура & Спа:</b>\n{features}\n\n"
        f"👶 <b>Для детей & Семьи:</b>\n{kid_friendly}\n\n"
        f"🎯 <b>Почему это топ:</b>\n<i>{why_best}</i>\n\n"
        f"💡 <b>Лайфхак бронирования:</b>\n<i>{tip}</i>\n\n"
        f"💬 <i>Вы можете задавать любые вопросы об этой локации (баня, бассейн, дети, собаки, аренда, ресторан, дорога) — консьерж ответит на всё!</i>"
    )

    kb = get_country_card_keyboard(category=category, geo_query=geo_query)
    await message.answer(card_text, parse_mode=ParseMode.HTML, reply_markup=kb)

