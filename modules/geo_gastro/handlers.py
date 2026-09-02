import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.geo_gastro.locator import find_places

logger = logging.getLogger("GeoGastroHandlers")
router = Router(name="geo_gastro")


def get_gastro_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🥩 Лучшие Мясные / Стейки", callback_data="gg_preset_meat"),
                InlineKeyboardButton(text="🍸 Секретные Спикизи-Бары", callback_data="gg_preset_speakeasy")
            ],
            [
                InlineKeyboardButton(text="🍕 Уютные Итальянские", callback_data="gg_preset_italian"),
                InlineKeyboardButton(text="🍜 Азиатские & Раменные", callback_data="gg_preset_asian")
            ],
            [
                InlineKeyboardButton(text="☕️ Спешелти Кофе & Завтраки", callback_data="gg_preset_coffee"),
                InlineKeyboardButton(text="🏙 Рестораны в Новосибирске", callback_data="gg_preset_nsk")
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
@router.message(F.text.in_(["📍 Рестораны", "📍 Гастро-Локатор", "Рестораны", "Кафе", "Спикизи-Бары", "Бары"]))
async def cmd_geo_gastro(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.geo_gastro_mode)
    text = (
        "📍 <b>Гастро-Локатор & Ресторанный Сомелье:</b>\n\n"
        "Я нахожу заведения, куда <b>реально стоит сходить</b> — с честным средним чеком, коронными блюдами и секретными фишками!\n\n"
        "💡 <b>Варианты поиска:</b>\n"
        "1. 📍 <b>Отправьте геопозицию</b> (кнопка ниже или скрепка 📎) — найду топ-заведения в радиусе 1 км от вас прямо сейчас!\n"
        "2. ✍️ <b>Напишите город / район / кухню:</b> <i>«Я в Новосибирске на Ленина»</i>, <i>«Где поесть стейки в Петроградке»</i>, <i>«Вкусная пицца в центре СПб»</i>.\n"
        "3. 🍸 <b>Нажмите кнопку «Секретные Спикизи-Бары»</b> для подбора баров с тайными входами и авторскими коктейлями!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_gastro_gps_keyboard())
    await message.answer("👇 <b>Категории и быстрый поиск:</b>", reply_markup=get_gastro_keyboard())


@router.callback_query(F.data.startswith("gg_preset_"))
async def cb_gastro_preset(callback: types.CallbackQuery, state: FSMContext):
    preset = callback.data.replace("gg_preset_", "")
    await state.set_state(ActiveModeStates.geo_gastro_mode)
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    
    presets = {
        "meat": ("Топ мясных ресторанов со смокером и стейками в Санкт-Петербурге", False),
        "speakeasy": ("Секретные спикизи бары Санкт-Петербурга с тайным входом и авторскими коктейлями", True),
        "italian": ("Лучшая неаполитанская пицца и паста ручной работы в СПб", False),
        "asian": ("Аутентичные раменные, паназия и суши в СПб", False),
        "coffee": ("Спешелти кофейни с фильтр-кофе и сытными завтраками весь день в СПб", False),
        "nsk": ("Легендарные и самые вкусные рестораны и бары Новосибирска (Красный проспект, ул. Ленина)", False)
    }
    query, is_speak = presets.get(preset, ("Лучшие рестораны СПб", False))
    await callback.answer("Подбираю заведения...")
    res = await find_places(callback.from_user.id, query, is_speakeasy=is_speak)
    await render_gastro_results(callback.message, res)


@router.message(ActiveModeStates.geo_gastro_mode, F.location)
async def handle_gastro_gps(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await find_places(message.from_user.id, f"Геолокация пользователя ({lat}, {lon})", lat=lat, lon=lon)
    await render_gastro_results(message, res)


@router.message(ActiveModeStates.geo_gastro_mode, F.text)
async def handle_gastro_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Гастро-Локатор» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    is_speak = "спикизи" in raw_text.lower() or "бар" in raw_text.lower() or "коктейл" in raw_text.lower()
    res = await find_places(message.from_user.id, raw_text, is_speakeasy=is_speak)
    await render_gastro_results(message, res)


async def render_gastro_results(message: types.Message, res: dict):
    summary = html.escape(str(res.get("search_summary", "Подборка заведений")))
    places = res.get("places", [])
    tip = html.escape(str(res.get("sommelier_tip", "")))

    lines = [
        f"🍽 <b>{summary.upper()}:</b>\n",
        "━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, p in enumerate(places, 1):
        name = html.escape(str(p.get("name", "Заведение")))
        p_type = html.escape(str(p.get("type", "")))
        rating = html.escape(str(p.get("rating", "⭐️ 4.8")))
        bill = html.escape(str(p.get("avg_bill", "")))
        dishes = html.escape(str(p.get("signature_dishes", "")))
        vibe = html.escape(str(p.get("vibe_description", "")))
        addr = html.escape(str(p.get("address", "")))

        lines.append(
            f"<b>{idx}. 🍷 {name}</b> <i>({p_type})</i>\n"
            f"   ⭐️ <b>Рейтинг:</b> {rating} | 💰 <b>Чек:</b> {bill}\n"
            f"   🥩 <b>Коронные блюда:</b> <i>{dishes}</i>\n"
            f"   ✨ <b>Вайб & Секреты:</b> {vibe}\n"
            f"   📍 <b>Адрес:</b> <code>{addr}</code>\n"
        )

    if tip:
        lines.append(f"💡 <b>Совет сомелье:</b>\n<i>{tip}</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_gastro_keyboard())
