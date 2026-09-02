import html
import logging
from aiogram import Router, types, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.keyboards import get_main_menu, get_mode_keyboard, is_exit_command
from core.states import ActiveModeStates
from modules.music_sommelier.generator import generate_music_playlist

logger = logging.getLogger("MusicSommelierHandlers")
router = Router(name="music_sommelier")


def get_music_keyboard(ym_url: str = "https://music.yandex.ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎵 Открыть в Яндекс Музыке", url=ym_url)
            ],
            [
                InlineKeyboardButton(text="🏎 Ночной ЗСД / КАД", callback_data="mus_drive"),
                InlineKeyboardButton(text="💻 Фокус для работы (Lo-Fi)", callback_data="mus_focus")
            ],
            [
                InlineKeyboardButton(text="🏋️‍♂️ Силовая тренировка", callback_data="mus_gym"),
                InlineKeyboardButton(text="🥩 Дача & Шашлык (Блюз-рок)", callback_data="mus_bbq")
            ],
            [
                InlineKeyboardButton(text="🚪 Главное меню", callback_data="mode_exit_to_main")
            ]
        ]
    )


@router.message(Command("music"))
@router.message(Command("playlist"))
@router.message(F.text.in_(["🎧 Музыка", "Музыка", "Музыкальный сомелье", "Плейлисты", "Плейлист"]))
async def cmd_music_sommelier(message: types.Message, state: FSMContext):
    await state.set_state(ActiveModeStates.music_sommelier_mode)
    text = (
        "🎧 <b>Музыкальный Сомелье & Генератор плейлистов под вайб:</b>\n\n"
        "Я составляю идеальные сеты треков под конкретные ситуации жизни с **прямой ссылкой на Яндекс.Музыку**!\n\n"
        "💡 <b>Примеры запросов:</b>\n"
        "• <i>«Музыка для ночной поездки на машине по Питеру»</i>\n"
        "• <i>«Глубокий фокус для кодинга без слов»</i>\n"
        "• <i>«Атмосферный вечерний джаз для ужина с бокалом вина»</i>\n"
        "• <i>«Бодрый фанк и блюз для шашлыков на природе»</i>\n\n"
        "💬 <i>Напишите ваше настроение или выберите готовый сет:</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_mode_keyboard("Музыка"))
    await message.answer("👇 <b>Готовые подборки под настроение:</b>", reply_markup=get_music_keyboard())


@router.callback_query(F.data.startswith("mus_"))
async def cb_music_preset(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ActiveModeStates.music_sommelier_mode)
    data = callback.data.replace("mus_", "")
    await callback.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    presets = {
        "drive": "Ночной прострел по ЗСД и КАД: плотный Synthwave, Phonk и Dark Disco",
        "focus": "Глубокая концентрация и рабочий фокус: Lo-Fi beats, Ambient и чистый инструментал",
        "gym": "Взрывная энергия для силовой тренировки: бодрый Hip-Hop, Rock и Phonk",
        "bbq": "Атмосферный день на даче у мангала: винтажный блюз-рок, фанк, инди и соул"
    }
    q = presets.get(data, "Лучшие музыкальные треки под настроение")
    await callback.answer("Миксую идеальный плейлист...")
    res = await generate_music_playlist(callback.from_user.id, q)
    await render_music_results(callback.message, res)


@router.message(ActiveModeStates.music_sommelier_mode, F.text)
async def handle_music_text(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    if is_exit_command(raw_text):
        await state.clear()
        if not raw_text.startswith("/"):
            await message.answer(
                "🏁 <b>Режим «Музыкальный сомелье» завершен.</b> Вы вернулись в главное меню.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu()
            )
        return

    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    res = await generate_music_playlist(message.from_user.id, raw_text)
    await render_music_results(message, res)


async def render_music_results(message: types.Message, res: dict):
    title = html.escape(str(res.get("playlist_title", "Плейлист")))
    vibe = html.escape(str(res.get("vibe_description", "")))
    ym_url = res.get("yandex_music_url", "https://music.yandex.ru")
    volume = html.escape(str(res.get("ideal_volume", "")))
    tracks = res.get("tracks", [])

    lines = [
        f"🎧 <b>{title.upper()}</b>\n",
        f"🎯 <b>Вайб сета:</b> <i>{vibe}</i>\n",
        "━━━━━━━━━━━━━━━━━━━",
        "🎵 <b>ТРЕК-ЛИСТ СЕТА:</b>"
    ]

    for idx, t in enumerate(tracks, 1):
        artist = html.escape(str(t.get("artist", "")))
        t_title = html.escape(str(t.get("title", "")))
        why = html.escape(str(t.get("why_match", "")))
        lines.append(f"<b>{idx}. 🎶 {artist} — {t_title}</b>\n   └ <i>{why}</i>")

    lines.append("")
    if volume:
        lines.append(f"🔊 <b>Рекомендация по звуку:</b> {volume}\n")

    lines.append("<i>👇 Нажмите кнопку ниже, чтобы мгновенно открыть этот поиск в Яндекс.Музыке:</i>")

    await message.answer("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=get_music_keyboard(ym_url))
