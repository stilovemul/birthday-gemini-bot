import io
import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.photo_spots.hunter import find_cinematic_photo_spots
from modules.photo_spots.storage import get_last_query, set_last_query

logger = logging.getLogger("PhotoSpotsHandlers")
router = Router(name="photo_spots")


def get_photo_start_keyboard() -> InlineKeyboardMarkup:
    """Стартовая клавиатура популярных категорий фото-спотов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Популярные локации СПб", callback_data="ps_preset_popular")
            ],
            [
                InlineKeyboardButton(text="🌊 Закаты на Финском заливе", callback_data="ps_preset_gulf"),
                InlineKeyboardButton(text="🏛 Парадные и крыши СПб", callback_data="ps_preset_roofs")
            ],
            [
                InlineKeyboardButton(text="🏙 Брутальный урбан & Неон", callback_data="ps_preset_neon"),
                InlineKeyboardButton(text="🌲 Скандинавская природа (ЛО)", callback_data="ps_preset_nature")
            ],
            [
                InlineKeyboardButton(text="🚗 Авто-Локации & Споттинг", callback_data="ps_preset_auto"),
                InlineKeyboardButton(text="☕️ Оранжереи & Эстетика", callback_data="ps_preset_coffee")
            ],
            [
                InlineKeyboardButton(text="🎲 Случайный спот сейчас", callback_data="ps_preset_random"),
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_photo_result_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура под готовой подборкой: кнопка «Другие споты (Ещё)» на первом месте."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Другие споты (Ещё)", callback_data="ps_more"),
                InlineKeyboardButton(text="🔥 Популярные", callback_data="ps_preset_popular")
            ],
            [
                InlineKeyboardButton(text="🌊 Залив", callback_data="ps_preset_gulf"),
                InlineKeyboardButton(text="🏛 Крыши", callback_data="ps_preset_roofs"),
                InlineKeyboardButton(text="🏙 Урбан", callback_data="ps_preset_neon")
            ],
            [
                InlineKeyboardButton(text="🌲 Природа", callback_data="ps_preset_nature"),
                InlineKeyboardButton(text="🚗 Авто", callback_data="ps_preset_auto"),
                InlineKeyboardButton(text="☕️ Оранжереи", callback_data="ps_preset_coffee")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("photospots"))
@router.message(Command("photo_locations"))
@router.message(F.text.in_(["📸 Фото-Споты", "Фото-Споты", "Фотолокации", "Красивые места", "Фотоспоты"]))
async def cmd_photo_spots(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.photo_spots_mode)
    text = (
        "📸 <b>Фото-Споты & Кинематографичные локации (СПб, ЛО и весь мир):</b>\n\n"
        "Я нахожу <b>самые эффектные точки для фото и рилс</b> с примерами кадров, точными координатами, "
        "лучшим светом, ракурсами, настройками оптики и ссылками на карты!\n\n"
        "💡 <b>Варианты поиска:</b>\n"
        "• 🔥 Нажмите кнопку <b>«🔥 Популярные локации СПб»</b> ниже\n"
        "• <i>«Кинематографичные места в центре СПб для мужской фотосессии»</i>\n"
        "• <i>«Где снять красивый закат у воды с машиной»</i>\n"
        "• <i>«Секретные видовые точки в Москве / Сочи / Дубае»</i>\n"
        "• 📸 <i>Отправьте фото-референс — найду похожие локации в СПб!</i>\n\n"
        "💬 <i>Напишите город/вайб или выберите категорию ниже:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Фото-Споты"))
    await message.answer("👇 <b>Популярные кинематографичные направления:</b>", parse_mode=ParseMode.HTML, reply_markup=get_photo_start_keyboard())


@router.callback_query(F.data == "ps_more")
async def cb_photo_more(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("🔄 Ищу новые локации и ракурсы...")
    await state.set_state(ActiveModeStates.photo_spots_mode)
    q = get_last_query(callback.from_user.id)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)
    res = await find_cinematic_photo_spots(callback.from_user.id, q)
    await render_photo_results(callback.message, res)


@router.callback_query(F.data.startswith("ps_preset_"))
async def cb_photo_preset(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("📸 Загружаю фотоспоты...")
    preset = callback.data.replace("ps_preset_", "")
    await state.set_state(ActiveModeStates.photo_spots_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_PHOTO)

    presets = {
        "popular": "Топ самых популярных и кинематографичных фотолокаций Санкт-Петербурга",
        "gulf": "Топ локаций на побережье Финского залива для закатных съемок с машиной и у воды",
        "roofs": "Лучшие легальные видовые крыши, террасы и исторические парадные Санкт-Петербурга",
        "neon": "Локации в стиле киберпанк, брутальный лофт, неон и ночные мосты в СПб",
        "nature": "Атмосферные природные локации Ленобласти: песчаные карьеры, сосновые дюны, скалы Выборга",
        "auto": "Топовые локации в СПб для фотосессии автомобиля: индустриальные паркинги, мосты, виды на Лахта Центр",
        "coffee": "Кинематографичные оранжереи, старинные книжные и эстетичные кофейни Санкт-Петербурга",
        "random": "Необычная секретная фотолокация Санкт-Петербурга с красивым светом и ракурсом"
    }
    q = presets.get(preset, "Кинематографичные фотолокации СПб")
    set_last_query(callback.from_user.id, q)
    res = await find_cinematic_photo_spots(callback.from_user.id, q)
    await render_photo_results(callback.message, res)


@router.callback_query(F.data == "mode_exit_to_main")
async def cb_mode_exit_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Главное меню")
    await callback.message.answer(
        "🏁 <b>Режим «Фото-Споты» завершен.</b> Вы вернулись в главное меню.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.message(StateFilter(ActiveModeStates.photo_spots_mode), F.photo)
async def handle_photo_vision(message: types.Message, state: FSMContext):
    """Анализ фото-референса через Gemini Vision и подбор похожих спотов."""
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    status_msg = await message.answer("🔍 <i>Анализирую цветовую гамму, свет и геометрию кадра...</i>", parse_mode=ParseMode.HTML)
    
    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=buf)
        img_bytes = buf.getvalue()
        
        user_prompt = (message.caption or "").strip()
        vibe_query = user_prompt if user_prompt else "Найди реальные фотолокации в Санкт-Петербурге и ЛО, передающие цветовую гамму, атмосферу и свет этого референса"
        set_last_query(message.from_user.id, vibe_query)
        
        res = await find_cinematic_photo_spots(message.from_user.id, vibe_query, image_bytes=img_bytes)
        try:
            await status_msg.delete()
        except Exception:
            pass
        await render_photo_results(message, res)
    except Exception as e:
        logger.error(f"Error analyzing photo reference: {e}")
        await message.answer(
            "⚠️ Не удалось проанализировать фото. Напишите текстовый запрос (например: <i>«Заброшенные цеха и неон»</i>):",
            parse_mode=ParseMode.HTML
        )


@router.message(StateFilter(ActiveModeStates.photo_spots_mode), F.text)
async def handle_photo_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Фото-Споты» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    # Текстовые триггеры ротации локаций
    raw_lower = raw_text.lower()
    rotation_triggers = [
        "еще", "ещё", "другой", "другие", "другие споты", "дальше",
        "покажи еще", "покажи ещё", "еще споты", "следующие", "еще варианты"
    ]
    if raw_lower in rotation_triggers:
        await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
        q = get_last_query(message.from_user.id)
        res = await find_cinematic_photo_spots(message.from_user.id, q)
        await render_photo_results(message, res)
        return

    set_last_query(message.from_user.id, raw_text)
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
    res = await find_cinematic_photo_spots(message.from_user.id, raw_text)
    await render_photo_results(message, res)


async def render_photo_results(message: types.Message, res: dict):
    title = html.escape(str(res.get("collection_title", "Фотолокации")))
    spots = res.get("spots", [])
    preset_tip = html.escape(str(res.get("editing_preset_tip", "")))

    lines = [
        f"📸 <b>{title.upper()}:</b>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, s in enumerate(spots, 1):
        name = html.escape(str(s.get("name", "Локация")))
        addr = html.escape(str(s.get("address_or_coords", "")))
        visual_desc = html.escape(str(s.get("visual_preview_desc", "")))
        style = html.escape(str(s.get("cinematic_style", "")))
        b_time = html.escape(str(s.get("best_time", "Золотой час")))
        angles = html.escape(str(s.get("camera_angles", "")))
        ideas = html.escape(str(s.get("photo_ideas", "")))
        access = html.escape(str(s.get("access_notes", "")))
        gear = html.escape(str(s.get("gear_tips", "")))
        map_url = s.get("map_url", "")
        photo_search_url = s.get("photo_search_url", "")

        links = []
        if map_url:
            links.append(f'<a href="{map_url}">📍 Карта ↗</a>')
        if photo_search_url:
            links.append(f'<a href="{photo_search_url}">🖼 Фотогалерея ракурсов ↗</a>')
        links_str = " | ".join(links)

        card_lines = [
            f"<b>{idx}. 🎬 {name}</b>",
            f"   📍 <b>Где:</b> <code>{addr}</code>" + (f"  [{links_str}]" if links_str else "")
        ]
        if visual_desc:
            card_lines.append(f"   👁 <b>Как выглядит:</b> <i>{visual_desc}</i>")
        if style:
            card_lines.append(f"   🎨 <b>Стиль:</b> <i>{style}</i>")
        if b_time:
            card_lines.append(f"   ⏰ <b>Лучший свет:</b> {b_time}")
        if angles:
            card_lines.append(f"   📐 <b>Ракурсы:</b> {angles}")
        if ideas:
            card_lines.append(f"   💡 <b>Идея кадра:</b> {ideas}")
        if gear:
            card_lines.append(f"   📷 <b>Оптика:</b> {gear}")
        if access:
            card_lines.append(f"   🚪 <b>Доступ:</b> {access}")
        card_lines.append("")

        lines.append("\n".join(card_lines))

    if preset_tip:
        lines.append(f"🎨 <b>Секрет цветокоррекции:</b>\n<i>{preset_tip}</i>\n")

    lines.append("<i>💡 Нажмите «🔄 Другие споты (Ещё)» или напишите «еще» для свежих ракурсов.</i>")

    full_text = "\n".join(lines)
    top_photo_url = spots[0].get("photo_url") if spots else None

    # Attempt to send with photo header if available
    sent_with_photo = False
    if top_photo_url:
        try:
            if len(full_text) <= 1024:
                await message.answer_photo(
                    photo=top_photo_url,
                    caption=full_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_photo_result_keyboard()
                )
                sent_with_photo = True
            else:
                header_caption = f"📸 <b>{title.upper()}</b>\n📍 <i>1. {html.escape(str(spots[0].get('name', '')))}</i>"
                await message.answer_photo(
                    photo=top_photo_url,
                    caption=header_caption,
                    parse_mode=ParseMode.HTML
                )
                await message.answer(
                    full_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_photo_result_keyboard(),
                    disable_web_page_preview=True
                )
                sent_with_photo = True
        except Exception as e:
            logger.warning(f"Failed to send photo for photo_spots: {e}")
            sent_with_photo = False

    if not sent_with_photo:
        await message.answer(
            full_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_photo_result_keyboard(),
            disable_web_page_preview=True
        )