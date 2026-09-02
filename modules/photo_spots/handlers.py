import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.photo_spots.hunter import find_cinematic_photo_spots

logger = logging.getLogger("PhotoSpotsHandlers")
router = Router(name="photo_spots")


def get_photo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌊 Закаты на Финском заливе", callback_data="ps_preset_gulf"),
                InlineKeyboardButton(text="🏛 Парадные и крыши СПб", callback_data="ps_preset_roofs")
            ],
            [
                InlineKeyboardButton(text="🏙 Брутальный урбан & Неон", callback_data="ps_preset_neon"),
                InlineKeyboardButton(text="🌲 Скандинавская природа (ЛО)", callback_data="ps_preset_nature")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("photospots"))
@router.message(Command("photo_locations"))
@router.message(F.text.in_(["📸 Фото-Споты", "Фото-Споты", "Фотолокации", "Красивые места"]))
async def cmd_photo_spots(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.photo_spots_mode)
    text = (
        "📸 <b>Фото-Споты & Кинематографичные локации (СПб, ЛО и весь мир):</b>\n\n"
        "Я нахожу **самые эффектные точки для фото и рилс** с точными координатами, лучшим светом и советами по ракурсам!\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Кинематографичные места в центре СПб для мужской фотосессии»</i>\n"
        "• <i>«Где снять красивый закат у воды с машиной»</i>\n"
        "• <i>«Секретные видовые точки в Москве / Сочи / Дубае»</i>\n\n"
        "💬 <i>Напишите город/вайб или выберите кнопку:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Фото-Споты"))
    await message.answer("👇 <b>Популярные локации:</b>", reply_markup=get_photo_keyboard())


@router.callback_query(F.data.startswith("ps_preset_"))
async def cb_photo_preset(callback: types.CallbackQuery, state: FSMContext):
    preset = callback.data.replace("ps_preset_", "")
    await state.set_state(ActiveModeStates.photo_spots_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    presets = {
        "gulf": "Топ локаций на побережье Финского залива для закатных съемок с машиной и у воды",
        "roofs": "Лучшие легальные видовые крыши, террасы и исторические парадные Санкт-Петербурга",
        "neon": "Локации в стиле киберпанк, брутальный лофт, неон и ночные мосты в СПб",
        "nature": "Атмосферные природные локации Ленобласти: песчаные карьеры, сосновые дюны, скалы Выборга"
    }
    q = presets.get(preset, "Кинематографичные фотолокации СПб")
    await callback.answer("Ищу лучшие фотоспоты...")
    res = await find_cinematic_photo_spots(callback.from_user.id, q)
    await render_photo_results(callback.message, res)


@router.message(ActiveModeStates.photo_spots_mode, F.text)
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

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
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
        style = html.escape(str(s.get("cinematic_style", "")))
        b_time = html.escape(str(s.get("best_time", "Золотой час")))
        angles = html.escape(str(s.get("camera_angles", "")))
        access = html.escape(str(s.get("access_notes", "")))

        lines.append(
            f"<b>{idx}. 🎬 {name}</b>\n"
            f"   📍 <b>Где:</b> <code>{addr}</code>\n"
            f"   🎨 <b>Стиль:</b> <i>{style}</i>\n"
            f"   ⏰ <b>Лучший свет:</b> {b_time}\n"
            f"   📐 <b>Ракурсы:</b> {angles}\n"
            f"   🚪 <b>Как попасть:</b> {access}\n"
        )

    if preset_tip:
        lines.append(f"🎨 <b>Секрет цветокоррекции:</b>\n<i>{preset_tip}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_photo_keyboard())
