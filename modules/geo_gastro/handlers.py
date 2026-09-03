import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.middlewares import is_menu_navigation
from core.states import ActiveModeStates
from modules.geo_gastro.locator import find_places
from modules.geo_gastro.storage import get_user_gastro_context, save_last_gastro_recommendations
from modules.geo_gastro.advisor import process_gastro_conversation
from modules.voice_assistant.transcriber import transcribe_audio_gemini

logger = logging.getLogger("GeoGastroHandlers")
router = Router(name="geo_gastro")


def get_gastro_qa_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard shown under gastro concierge answers for continuous dialogue or quick actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другие заведения рядом (Ещё)", callback_data="gg_more")
            ],
            [
                InlineKeyboardButton(text="🥩 Стейки", callback_data="gg_preset_meat"),
                InlineKeyboardButton(text="🍸 Спикизи-Бары", callback_data="gg_preset_speakeasy")
            ],
            [
                InlineKeyboardButton(text="🍕 Итальянские", callback_data="gg_preset_italian"),
                InlineKeyboardButton(text="🍜 Азиатские", callback_data="gg_preset_asian")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )



def get_gastro_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другие заведения рядом (Ещё)", callback_data="gg_more")
            ],
            [
                InlineKeyboardButton(text="🥩 Стейки & Мясо", callback_data="gg_preset_meat"),
                InlineKeyboardButton(text="🍸 Секретные Спикизи", callback_data="gg_preset_speakeasy")
            ],
            [
                InlineKeyboardButton(text="🍕 Итальянские & Пицца", callback_data="gg_preset_italian"),
                InlineKeyboardButton(text="🍜 Азиатские & Рамен", callback_data="gg_preset_asian")
            ],
            [
                InlineKeyboardButton(text="☕️ Кофе & Завтраки", callback_data="gg_preset_coffee"),
                InlineKeyboardButton(text="🏙 Новосибирск", callback_data="gg_preset_nsk")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_gastro_gps_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Найти рестораны рядом со мной (GPS)", request_location=True)],
            [KeyboardButton(text="🏁 Закончить режим (Главное меню)")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )


@router.message(Command("restaurants"))
@router.message(Command("cafe"))
@router.message(Command("bars"))
@router.message(Command("gastro"))
@router.message(F.text.func(lambda t: t and any(w in t.lower() for w in [
    "📍 рестораны", "рестораны", "гастро-локатор", "гастролокатор", "кафе", "спикизи", "спикизи-бары", "бары", "где поесть"
])))
async def cmd_geo_gastro(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.geo_gastro_mode)
    text = (
        "📍 <b>Гастро-Локатор & Ресторанный Сомелье:</b>\n\n"
        "Я нахожу заведения, куда <b>реально стоит сходить</b> — с честным средним чеком, коронными блюдами и секретными фишками!\n\n"
        "💡 <b>Варианты поиска:</b>\n"
        "1. 📍 <b>Отправьте геопозицию</b> (кнопка ниже или скрепка 📎) — найду топ-заведения в радиусе 1–2 км от вас прямо сейчас!\n"
        "2. ✍️ <b>Напишите город / район / кухню:</b> <i>«Я в Новосибирске на Ленина»</i>, <i>«Где поесть стейки в Петроградке»</i>, <i>«Вкусная пицца в центре СПб»</i>.\n"
        "3. 🍸 <b>Нажмите кнопку «Секретные Спикизи»</b> для подбора баров с тайными входами и авторскими коктейлями!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_gastro_gps_keyboard())
    await message.answer("👇 <b>Категории и быстрый поиск:</b>", parse_mode=ParseMode.HTML, reply_markup=get_gastro_keyboard())


@router.callback_query(F.data.startswith("gg_preset_"))
async def cb_gastro_preset(callback: types.CallbackQuery, state: FSMContext):
    preset = callback.data.replace("gg_preset_", "")
    await state.set_state(ActiveModeStates.geo_gastro_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    presets = {
        "meat": ("Топ мясных ресторанов со смокером и стейками", False, "meat"),
        "speakeasy": ("Секретные спикизи бары с тайным входом и авторскими коктейлями", True, "speakeasy"),
        "italian": ("Лучшая неаполитанская пицца и паста ручной работы", False, "italian"),
        "asian": ("Аутентичные раменные, паназия и суши", False, "asian"),
        "coffee": ("Спешелти кофейни с фильтр-кофе и сытными завтраками весь день", False, "coffee"),
        "nsk": ("Легендарные рестораны и бары Новосибирска (ул. Ленина, Красный проспект)", False, "nsk")
    }
    query, is_speak, cat = presets.get(preset, ("Лучшие рестораны", False, "all"))
    await callback.answer("Подбираю заведения...")
    res = await find_places(callback.from_user.id, query, is_speakeasy=is_speak, category=cat)
    await render_gastro_results(callback.message, res)


@router.callback_query(F.data == "gg_more")
async def cb_gastro_more(callback: types.CallbackQuery, state: FSMContext):
    """Подбор других заведений (кнопка «Ещё» без повторов)."""
    await state.set_state(ActiveModeStates.geo_gastro_mode)
    await callback.answer("🔄 Подбираю другие заведения рядом...")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    ctx = get_user_gastro_context(callback.from_user.id)
    cat = ctx.get("last_category") or "all"
    query = ctx.get("last_query") or "рядом со мной"
    res = await find_places(callback.from_user.id, query, is_more=True, category=cat)
    await render_gastro_results(callback.message, res)


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_exit_gastro(callback: types.CallbackQuery, state: FSMContext):
    """Выход из режима «Гастро-Локатор» в главное меню."""
    await state.clear()
    await callback.answer("Вы вышли в главное меню")
    await callback.message.answer(
        "🏁 <b>Режим «Гастро-Локатор» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.message(ActiveModeStates.geo_gastro_mode, F.location)
async def handle_gastro_gps(message: types.Message, state: FSMContext):
    """Обработка точной GPS-геопозиции в модуле ресторанов."""
    lat = float(message.location.latitude)
    lon = float(message.location.longitude)
    user_id = message.from_user.id

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    status_msg = await message.answer(
        "📍 <b>Геопозиция определена!</b> 🛰️✨\n"
        "🔍 <i>Сканирую гастрономическую карту и подбираю топ-заведения в радиусе 1–2 км от вас...</i>",
        parse_mode=ParseMode.HTML
    )
    
    res = await find_places(user_id, "рядом со мной", lat=lat, lon=lon, category="all")
    try:
        await status_msg.delete()
    except Exception:
        pass

    await render_gastro_results(message, res)


@router.message(ActiveModeStates.geo_gastro_mode, F.text)
async def handle_gastro_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text) or is_menu_navigation(raw_text):
        await state.clear()
        if is_exit_command(raw_text) and not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Гастро-Локатор» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    t_lower = raw_text.lower()
    more_triggers = [
        "еще", "ещё", "другой", "другие", "дальше", "следующий", "вариант",
        "покажи еще", "еще заведения", "ещё заведения", "другие рестораны"
    ]
    if t_lower in more_triggers:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        ctx = get_user_gastro_context(message.from_user.id)
        cat = ctx.get("last_category") or "all"
        query = ctx.get("last_query") or "рядом со мной"
        res = await find_places(message.from_user.id, query, is_more=True, category=cat)
        await render_gastro_results(message, res)
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    # 1. Проверяем, задает ли пользователь вопрос по текущей подборке заведений (интерактивный диалог)
    is_followup, ans_or_query = await process_gastro_conversation(message.from_user.id, raw_text)
    if is_followup and ans_or_query:
        await message.answer(ans_or_query, parse_mode=ParseMode.HTML, reply_markup=get_gastro_qa_keyboard())
        return

    # 2. Иначе это новый поисковый запрос (другая кухня или район)
    search_query = ans_or_query or raw_text
    is_speak = "спикизи" in search_query.lower() or "бар" in search_query.lower() or "коктейл" in search_query.lower()
    cat = "speakeasy" if is_speak else "all"
    res = await find_places(message.from_user.id, search_query, is_speakeasy=is_speak, category=cat)
    await render_gastro_results(message, res)


@router.message(ActiveModeStates.geo_gastro_mode, F.voice | F.video_note | F.audio)
async def handle_gastro_voice(message: types.Message, state: FSMContext):
    """Обработка голосовых вопросов и запросов в режиме Гастро-Локатора."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    audio_obj = message.voice or message.video_note or message.audio
    try:
        file = await message.bot.get_file(audio_obj.file_id)
        file_bytes_io = await message.bot.download_file(file.file_path)
        audio_bytes = file_bytes_io.read()
    except Exception as e:
        logger.warning(f"Error downloading voice message: {e}")
        await message.answer("⚠️ Не удалось загрузить аудиосообщение. Напишите, пожалуйста, текстом.")
        return

    transcribed = await transcribe_audio_gemini(audio_bytes)
    if not transcribed:
        await message.answer("🎙 Не удалось расслышать голосовое сообщение. Попробуйте повторить или написать текстом.")
        return

    await message.answer(f"🎙 <b>Вы спросили:</b> <i>«{html.escape(transcribed)}»</i>", parse_mode=ParseMode.HTML)
    
    # Передаем транскрибированный текст в консьерж-диалог
    is_followup, ans_or_query = await process_gastro_conversation(message.from_user.id, transcribed)
    if is_followup and ans_or_query:
        await message.answer(ans_or_query, parse_mode=ParseMode.HTML, reply_markup=get_gastro_qa_keyboard())
        return

    search_query = ans_or_query or transcribed
    is_speak = "спикизи" in search_query.lower() or "бар" in search_query.lower() or "коктейл" in search_query.lower()
    cat = "speakeasy" if is_speak else "all"
    res = await find_places(message.from_user.id, search_query, is_speakeasy=is_speak, category=cat)
    await render_gastro_results(message, res)


async def render_gastro_results(message: types.Message, res: dict):
    summary = html.escape(str(res.get("search_summary", "Подборка заведений")))
    places = res.get("places", [])
    tip = html.escape(str(res.get("sommelier_tip", "")))
    human_loc = html.escape(str(res.get("human_location", "")))

    # Сохраняем подборку в память для интерактивного диалога и вопросов
    user_id = message.chat.id
    save_last_gastro_recommendations(user_id, places, summary=summary, tip=tip)

    lines = [
        f"🍽 <b>{summary.upper()}</b>",
    ]
    if human_loc and human_loc.lower() not in summary.lower():
        lines.append(f"📍 <i>Локация: {human_loc}</i>")
    lines.append("━━━━━━━━━━━━━━━━━━━")

    for idx, p in enumerate(places, 1):
        name = html.escape(str(p.get("name", "Заведение")))
        p_type = html.escape(str(p.get("type", "")))
        rating = html.escape(str(p.get("rating", "⭐️ 4.8")))
        bill = html.escape(str(p.get("avg_bill", "")))
        distance = html.escape(str(p.get("distance", "")))
        dishes = html.escape(str(p.get("signature_dishes", "")))
        vibe = html.escape(str(p.get("vibe_description", "")))
        addr = html.escape(str(p.get("address", "")))
        map_url = p.get("map_url", "")

        dist_str = f" | 🚶‍♂️ <i>{distance}</i>" if distance else ""
        if map_url:
            addr_line = f"📍 <b>Адрес:</b> <a href=\"{map_url}\"><code>{addr}</code> ↗</a>"
        else:
            addr_line = f"📍 <b>Адрес:</b> <code>{addr}</code>"

        lines.append(
            f"<b>{idx}. 🍷 {name}</b> <i>({p_type})</i>\n"
            f"   ⭐️ <b>Рейтинг:</b> {rating} | 💰 <b>Чек:</b> {bill}{dist_str}\n"
            f"   🥩 <b>Коронные блюда:</b> <i>{dishes}</i>\n"
            f"   ✨ <b>Вайб & Секреты:</b> {vibe}\n"
            f"   {addr_line}\n"
        )

    if tip:
        lines.append(f"💡 <b>Совет сомелье:</b>\n<i>{tip}</i>\n")

    lines.append("💬 <i>Вы можете задать любой вопрос о заведениях (меню, бронь, вино, дети, парковка) или назвать новую локацию!</i>")

    await message.answer(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=get_gastro_keyboard(),
        disable_web_page_preview=True
    )

