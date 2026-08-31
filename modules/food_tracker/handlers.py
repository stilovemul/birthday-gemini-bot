import logging
import io
from typing import Dict, Any
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.food_tracker.storage import (
    log_meal,
    get_daily_summary,
    delete_meal,
    clear_today_meals,
    get_user_calorie_goal,
    set_user_calorie_goal
)
from modules.food_tracker.analyzer import analyze_food_photo

logger = logging.getLogger("FoodHandler")
router = Router(name="food_tracker")


def get_food_meal_keyboard(meal_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Дневной рацион", callback_data="food_show_today"),
                InlineKeyboardButton(text="🗑 Удалить запись", callback_data=f"food_del_{meal_id}")
            ]
        ]
    )


def format_daily_summary_text(summary: Dict[str, Any]) -> str:
    total_kcal = summary["total_calories"]
    goal = summary["goal_calories"]
    rem = summary["remaining_calories"]
    p = summary["total_protein"]
    f = summary["total_fat"]
    c = summary["total_carbs"]
    meals = summary["meals"]

    # Progress bar
    pct = min(100, int((total_kcal / goal) * 100)) if goal > 0 else 0
    filled = int(pct / 10)
    bar = "🟩" * filled + "⬜" * (10 - filled)

    lines = [
        f"📊 <b>Рацион за сегодня ({summary['date']}):</b>\n",
        f"🔥 <b>Калории:</b> <code>{total_kcal} / {goal} ккал</code> ({pct}%)",
        f"[{bar}]\n",
        f"🥩 <b>Белки:</b> <code>{p} г</code>",
        f"🧈 <b>Жиры:</b> <code>{f} г</code>",
        f"🍞 <b>Углеводы:</b> <code>{c} г</code>",
        f"🎯 <b>Осталось до нормы:</b> <code>{rem} ккал</code>\n",
        "🍽 <b>Приёмы пищи:</b>"
    ]

    if not meals:
        lines.append("<i>Пока нет записей. Просто пришлите фото вашей еды!</i>")
    else:
        for idx, m in enumerate(meals, 1):
            lines.append(f"{idx}. 🕒 <b>{m['time']}</b> — <b>{m['dish_name']}</b>: <code>{m['calories']} ккал</code> (Б:{m['protein']} Ж:{m['fat']} У:{m['carbs']})")

    lines.append("\n💡 <i>Чтобы добавить приём пищи — сфотографируйте вашу тарелку и отправьте в чат!</i>")
    return "\n".join(lines)


@router.message(Command("food"))
@router.message(Command("calories"))
@router.message(Command("today_food"))
@router.message(F.text == "🥗 Сканер еды & КБЖУ")
async def cmd_food_menu(message: types.Message):
    user_id = message.from_user.id
    summary = get_daily_summary(user_id)
    text = format_daily_summary_text(summary)
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎯 Изменить цель калорий", callback_data="food_set_goal_hint"),
                InlineKeyboardButton(text="🧹 Очистить сегодня", callback_data="food_clear_today")
            ]
        ]
    )
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.message(Command("set_goal"))
@router.message(Command("food_goal"))
async def cmd_set_goal(message: types.Message):
    args = (message.text or "").split()
    user_id = message.from_user.id
    if len(args) > 1 and args[1].isdigit():
        new_goal = int(args[1])
        set_user_calorie_goal(user_id, new_goal)
        await message.answer(
            f"✅ <b>Дневная цель обновлена:</b> <code>{new_goal} ккал</code>!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )
    else:
        curr = get_user_calorie_goal(user_id)
        await message.answer(
            f"🎯 <b>Ваша текущая норма:</b> <code>{curr} ккал</code>.\n\n"
            "Чтобы изменить, напишите: <code>/set_goal 2000</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data == "food_show_today")
async def callback_show_today(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    summary = get_daily_summary(user_id)
    text = format_daily_summary_text(summary)
    await callback.message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "food_set_goal_hint")
async def callback_set_goal_hint(callback: types.CallbackQuery):
    curr = get_user_calorie_goal(callback.from_user.id)
    await callback.answer(f"Текущая цель: {curr} ккал. Напишите /set_goal ЧИСЛО", show_alert=True)


@router.callback_query(F.data == "food_clear_today")
async def callback_clear_today(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    count = clear_today_meals(user_id)
    await callback.answer(f"Удалено записей: {count}")
    await callback.message.answer("🧹 <b>Дневной рацион на сегодня очищен!</b>", parse_mode=ParseMode.HTML, reply_markup=get_main_menu())


@router.callback_query(F.data.startswith("food_del_"))
async def callback_delete_meal(callback: types.CallbackQuery):
    meal_id = callback.data.replace("food_del_", "")
    user_id = callback.from_user.id
    success = delete_meal(user_id, meal_id)
    if success:
        await callback.answer("Запись о приёме пищи удалена!")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("🗑 <i>Запись удалена из суточного подсчёта.</i>", parse_mode=ParseMode.HTML)
    else:
        await callback.answer("Запись не найдена или уже была удалена.")
