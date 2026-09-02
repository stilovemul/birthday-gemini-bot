import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.mystic_spb.storyteller import get_mystic_spb_story

logger = logging.getLogger("MysticSPBHandlers")
router = Router(name="mystic_spb")


def get_mystic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📍 Гостиница Англетер (Есенин)", callback_data="mspb_loc_angleterre"),
                InlineKeyboardButton(text="🏛 Манежная площадь", callback_data="mspb_loc_manezhnaya")
            ],
            [
                InlineKeyboardButton(text="🏰 Юсуповский дворец (Распутин)", callback_data="mspb_loc_yusupov"),
                InlineKeyboardButton(text="👻 Михайловский замок (Павел I)", callback_data="mspb_loc_castle")
            ],
            [
                InlineKeyboardButton(text="🔫 Черная речка (Пушкин)", callback_data="mspb_loc_pushkin"),
                InlineKeyboardButton(text="🎲 Случайная тайна СПб", callback_data="mspb_loc_random")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


def get_spb_gps_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить мою геопозицию", request_location=True)],
            [KeyboardButton(text="🏁 Закончить режим (Главное меню)")]
        ],
        resize_keyboard=True,
        is_persistent=False
    )


@router.message(Command("spb_mystic"))
@router.message(Command("spb"))
@router.message(F.text.in_(["🕵️‍♂️ Тайный СПб", "Тайный СПб", "Мистический Петербург", "Мистический СПб", "Легенды СПб"]))
async def cmd_mystic_spb(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.mystic_spb_mode)
    text = (
        "🕵️‍♂️ <b>Тайный, Исторический & Мистический Петербург:</b>\n\n"
        "Я ваш персональный сталкер и эксперт по <b>городским тайнам, расследованиям «ЗА и ПРОТИВ», бандитскому следу и визуальной машине времени «Тогда vs Сейчас»</b>!\n\n"
        "💡 <b>Как пользоваться:</b>\n"
        "1. 📍 <b>Нажмите кнопку отправки геопозиции</b> (или скрепка 📎 ➔ «Геопозиция») прямо на улице — я мгновенно расскажу тайны места вокруг вас!\n"
        "2. ✍️ <b>Напишите любое место/улицу:</b> <i>«Англетер»</i>, <i>«Манежная площадь»</i>, <i>«Ротонда на Гороховой»</i>, <i>«Сенная»</i>, <i>«Лиговка»</i>.\n"
        "3. 🔘 <b>Или выберите знаменитую тайну на кнопках ниже!</b>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_spb_gps_mode_keyboard())
    await message.answer("👇 <b>Популярные мистические и детективные локации:</b>", reply_markup=get_mystic_keyboard())


@router.callback_query(F.data.startswith("mspb_loc_"))
async def cb_mystic_preset(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.mystic_spb_mode)
    loc_key = callback.data.replace("mspb_loc_", "")
    preset_names = {
        "angleterre": "Гостиница Англетер, Исаакиевская площадь (Тайна гибели Сергея Есенина)",
        "manezhnaya": "Манежная площадь и Итальянская улица, Санкт-Петербург",
        "yusupov": "Юсуповский дворец на Мойке (Убийство Григория Распутина)",
        "castle": "Михайловский (Инженерный) замок (Заговор и призрак Павла I)",
        "pushkin": "Место дуэли Пушкина на Черной речке и Комендантская дача",
        "random": "Секретный мистический двор и криминальная легенда центра Санкт-Петербурга"
    }
    query = preset_names.get(loc_key, "Тайны Санкт-Петербурга")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)
    await callback.answer(f"Исследую {query[:30]}...")
    res = await get_mystic_spb_story(callback.from_user.id, query)
    await render_mystic_story(callback.message, res)


@router.message(ActiveModeStates.mystic_spb_mode, F.location)
async def handle_spb_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await get_mystic_spb_story(message.from_user.id, f"Геолокация пользователя в Санкт-Петербурге ({lat}, {lon})", lat=lat, lon=lon)
    await render_mystic_story(message, res)


@router.message(ActiveModeStates.mystic_spb_mode, F.text)
async def handle_spb_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Тайный Петербург» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await get_mystic_spb_story(message.from_user.id, raw_text)
    await render_mystic_story(message, res)


async def render_mystic_story(message: types.Message, res: dict):
    loc_name = html.escape(str(res.get("location_name", "Санкт-Петербург")))
    origin = html.escape(str(res.get("name_origin", "")))
    chronicle = html.escape(str(res.get("era_chronicle", "")))
    invest = res.get("historical_investigation", {})
    inv_title = html.escape(str(invest.get("title", "Историческое расследование")))
    facts_pro = html.escape(str(invest.get("facts_pro", "")))
    facts_contra = html.escape(str(invest.get("facts_contra", "")))
    crime = html.escape(str(res.get("crime_and_legends", "")))
    then_now = html.escape(str(res.get("then_and_now_visual", "")))
    secret = html.escape(str(res.get("secret_doorway", "")))
    route = html.escape(str(res.get("next_quest_route", "")))

    lines = [
        f"🏛 <b>{loc_name.upper()}</b>\n",
        f"📍 <b>Откуда пошло название:</b>\n<i>{origin}</i>\n",
        f"📜 <b>Хроника сквозь эпохи:</b>\n{chronicle}\n",
        "━━━━━━━━━━━━━━━━━━━",
        f"⚖️ <b>РАССЛЕДОВАНИЕ: «{inv_title}»</b>",
        f"🟢 <b>Версия ЗА:</b> {facts_pro}",
        f"🔴 <b>Факты ПРОТИВ / Тайная версия:</b> {facts_contra}\n",
        "━━━━━━━━━━━━━━━━━━━",
        f"💀 <b>Криминальный след & Мистика:</b>\n{crime}\n",
        f"📸 <b>ВИЗУАЛЬНО «ТОГДА И СЕЙЧАС» (Машина времени):</b>\n<i>{then_now}</i>\n",
        f"👁 <b>Секретная пасхалка рядом:</b>\n👉 {secret}\n",
        f"🚶‍♂️ <b>Пеший маршрут-квест дальше (на 30–40 мин):</b>\n{route}"
    ]

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_mystic_keyboard())
