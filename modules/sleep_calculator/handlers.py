import re
import logging
from datetime import datetime, timedelta
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.config import MSK_TZ
from core.keyboards import get_main_menu
from modules.sleep_calculator.calculator import (
    calculate_bedtimes_for_wakeup,
    calculate_wakeups_from_now,
    get_power_naps
)
from modules.smart_reminders.storage import add_reminder

logger = logging.getLogger("SleepHandlers")
router = Router(name="sleep_calculator")


def get_sleep_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌙 Ложусь прямо сейчас", callback_data="slp_now"),
                InlineKeyboardButton(text="⏰ Выбрать время подъема", callback_data="slp_choose_wake")
            ],
            [
                InlineKeyboardButton(text="⚡ Дневной Power Nap", callback_data="slp_nap"),
                InlineKeyboardButton(text="💡 Наука сна и биоритмы", callback_data="slp_tips")
            ]
        ]
    )


def get_wakeup_presets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 06:00", callback_data="slp_w_06:00"),
                InlineKeyboardButton(text="🌅 06:30", callback_data="slp_w_06:30"),
                InlineKeyboardButton(text="⏰ 07:00", callback_data="slp_w_07:00")
            ],
            [
                InlineKeyboardButton(text="⏰ 07:30", callback_data="slp_w_07:30"),
                InlineKeyboardButton(text="☀️ 08:00", callback_data="slp_w_08:00"),
                InlineKeyboardButton(text="☀️ 08:30", callback_data="slp_w_08:30")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="slp_back_main")
            ]
        ]
    )


def format_bedtimes_report(wake_str: str, results: list) -> str:
    lines = [
        f"⏰ <b>Чтобы легко проснуться в {wake_str}:</b>\n",
        "Человеческий сон состоит из 90-минутных циклов. Чтобы проснуться бодрым и полным энергии, нужно ложиться в одно из следующих значений <i>(с учётом ~14 минут на засыпание)</i>:\n"
    ]
    for r in results:
        lines.append(f"• 🛌 <b>{r['bed_time_str']}</b> — {r['quality']}")
        lines.append(f"  <i>({r['desc']})</i>\n")

    lines.append("💡 <i>Нажмите кнопку ниже, чтобы поставить умное напоминание лечь спать!</i>")
    return "\n".join(lines)


@router.message(Command("sleep"))
@router.message(Command("sleep_calc"))
@router.message(F.text == "😴 Калькулятор сна")
async def cmd_sleep_calculator(message: types.Message):
    args = (message.text or "").split(maxsplit=1)

    # If user provided a specific time, e.g. /sleep 07:00 or /sleep 7:30
    if len(args) > 1 and args[1].strip() and args[1].strip() != "Калькулятор сна":
        time_match = re.search(r"(\d{1,2})[:.-](\d{2})", args[1].strip())
        if time_match:
            h = int(time_match.group(1))
            m = int(time_match.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                wake_str, results = calculate_bedtimes_for_wakeup(h, m)
                report = format_bedtimes_report(wake_str, results)
                # Remind buttons for top 2 options
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text=f"⏰ Напомнить в {results[1]['bed_time_str']}", callback_data=f"slp_set_rem_{results[1]['bed_time_str']}"),
                            InlineKeyboardButton(text=f"⏰ Напомнить в {results[2]['bed_time_str']}", callback_data=f"slp_set_rem_{results[2]['bed_time_str']}")
                        ],
                        [InlineKeyboardButton(text="🔙 Меню сна", callback_data="slp_back_main")]
                    ]
                )
                await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=kb)
                return

    intro = (
        "😴 <b>Умный калькулятор фаз сна & Биоритмы</b> 🌙\n\n"
        "Правильный сон — это не просто количество часов, а **завершённые 90-минутные циклы**.\n"
        "Если будильник звенит в середине фазы глубокого сна — вы чувствуете себя разбитым весь день. Если в конце цикла — просыпаетесь легко и с ясной головой! ⚡\n\n"
        "👇 <b>Выберите действие:</b>"
    )
    await message.answer(intro, parse_mode=ParseMode.HTML, reply_markup=get_sleep_main_keyboard())


@router.callback_query(F.data == "slp_now")
async def callback_sleep_now(callback: types.CallbackQuery):
    now_str, results = calculate_wakeups_from_now()
    lines = [
        f"🌙 <b>Если вы ляжете спать прямо сейчас ({now_str}):</b>\n",
        "С учётом ~14 минут на засыпание, идеальное время для лёгкого пробуждения по фазам сна:\n"
    ]
    for r in results:
        lines.append(f"• ⏰ <b>{r['wake_time_str']}</b> — {r['quality']}")
        lines.append(f"  <i>({r['desc']})</i>\n")

    lines.append("💤 <i>Поставьте будильник на одно из этих значений и ложитесь отдыхать!</i>")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="slp_back_main")]
        ]
    )
    await callback.message.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "slp_choose_wake")
async def callback_choose_wake(callback: types.CallbackQuery):
    text = (
        "⏰ <b>Во сколько вам нужно проснуться?</b>\n\n"
        "Выберите удобное время из кнопок ниже или отправьте команду с любым временем (например: <code>/sleep 07:15</code>):"
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=get_wakeup_presets_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("slp_w_"))
async def callback_preset_wakeup(callback: types.CallbackQuery):
    time_val = callback.data.replace("slp_w_", "")
    h, m = map(int, time_val.split(":"))
    wake_str, results = calculate_bedtimes_for_wakeup(h, m)
    report = format_bedtimes_report(wake_str, results)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"⏰ Напомнить в {results[1]['bed_time_str']}", callback_data=f"slp_set_rem_{results[1]['bed_time_str']}"),
                InlineKeyboardButton(text=f"⏰ Напомнить в {results[2]['bed_time_str']}", callback_data=f"slp_set_rem_{results[2]['bed_time_str']}")
            ],
            [InlineKeyboardButton(text="🔙 Выбрать другое время", callback_data="slp_choose_wake")]
        ]
    )
    await callback.message.edit_text(report, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("slp_set_rem_"))
async def callback_set_sleep_reminder(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    target_time_str = callback.data.replace("slp_set_rem_", "")
    
    # Calculate target datetime today or tomorrow
    now = datetime.now(MSK_TZ)
    h, m = map(int, target_time_str.split(":"))
    target_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target_dt <= now:
        target_dt += timedelta(days=1)

    add_reminder(
        user_id=user_id,
        text=f"🛌 Пора готовиться ко сну ({target_time_str})! Выключите экраны и ложитесь отдыхать для лёгкого подъема 🌙",
        target_dt=target_dt,
        target_display=f"{target_dt.strftime('%d.%m')} в {target_time_str} MSK"
    )

    await callback.answer(f"Напоминание установлено на {target_time_str} MSK! ⏰", show_alert=True)
    await callback.message.answer(
        f"✅ <b>Напоминание создано!</b>\n\n"
        f"Бот пришлёт уведомление сегодня в <b>{target_time_str} MSK</b>, чтобы вы вовремя легли спать и проснулись полным сил! 🛌✨",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "slp_nap")
async def callback_power_nap(callback: types.CallbackQuery):
    now_str, naps = get_power_naps()
    lines = [
        f"⚡ <b>Дневной восстановительный сон (Power Nap) — {now_str} MSK</b>\n",
        "Дневной сон может дать колоссальный прилив сил, если не переходить в медленную фазу:\n"
    ]
    for n in naps:
        lines.append(f"• <b>{n['name']}</b>")
        lines.append(f"  🕒 Поставьте будильник на: <b>{n['wake_time']}</b>")
        lines.append(f"  <i>{n['desc']}</i>\n")

    lines.append("☕ <b>Секретный лайфхак (Кофе-нап):</b> выпейте чашку эспрессо прямо перед 20-минутным сном. Кофеин начинает действовать ровно через 20 минут, и вы проснетесь с двойной энергией!")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В меню сна", callback_data="slp_back_main")]
        ]
    )
    await callback.message.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "slp_tips")
async def callback_sleep_tips(callback: types.CallbackQuery):
    tips_text = (
        "💡 <b>5 научных правил для глубокого и качественного сна:</b>\n\n"
        "1. 📱 <b>Правило синего света:</b> выключайте смартфон и яркий экран за 45 минут до сна (синий спектр блокирует выработку мелатонина).\n"
        "2. 🌡 <b>Температура в спальне:</b> идеальная температура для выработки гормона сна — <b>18–20°C</b> с проветренной комнатой.\n"
        "3. ☕ <b>Кофеиновый лимит:</b> прекращайте пить кофе и крепкий чай за 6–8 часов до отхода ко сну.\n"
        "4. 🧘 <b>Правило постоянства:</b> старайтесь ложиться и вставать в одно и то же время даже в выходные (±30 минут).\n"
        "5. 🍽 <b>Легкий ужин:</b> последний приём пищи должен быть за 2.5–3 часа до сна."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В меню сна", callback_data="slp_back_main")]
        ]
    )
    await callback.message.edit_text(tips_text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "slp_back_main")
async def callback_back_main(callback: types.CallbackQuery):
    intro = (
        "😴 <b>Умный калькулятор фаз сна & Биоритмы</b> 🌙\n\n"
        "Правильный сон — это завершённые 90-минутные циклы.\n\n"
        "👇 <b>Выберите действие:</b>"
    )
    await callback.message.edit_text(intro, parse_mode=ParseMode.HTML, reply_markup=get_sleep_main_keyboard())
    await callback.answer()
