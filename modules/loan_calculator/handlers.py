import logging
from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.keyboards import get_main_menu
from modules.loan_calculator.calculator import (
    calculate_annuity_loan,
    calculate_early_repayment_savings,
    parse_loan_query
)

logger = logging.getLogger("LoanHandlers")
router = Router(name="loan_calculator")

# User FSM wizard states
user_loan_wizard: dict = {}


def format_rubles(val: float) -> str:
    return f"{int(val):,}".replace(",", " ") + " ₽"


def format_loan_result(data: dict) -> str:
    base = data.get("base", data)
    has_early = data.get("has_early", False)

    amount_str = format_rubles(base['amount'])
    monthly_str = format_rubles(base['monthly_payment'])
    overpayment_str = format_rubles(base['total_overpayment'])
    total_str = format_rubles(base['total_payout'])

    lines = [
        f"📊 <b>Расчет кредита / ипотеки:</b>\n",
        f"💰 <b>Сумма кредита:</b> <code>{amount_str}</code>",
        f"📈 <b>Процентная ставка:</b> <code>{base['annual_rate']}%</code> годовых",
        f"⏳ <b>Срок кредита:</b> <code>{base['years']} лет</code> ({base['months']} мес.)\n",
        "───────────────────────",
        f"💳 <b>Ежемесячный платёж:</b> <code>{monthly_str}</code>",
        f"💸 <b>Переплата по процентам:</b> <b>{overpayment_str}</b> (+{base['overpayment_percent']}%)",
        f"💵 <b>Всего выплат банку:</b> <b>{total_str}</b>",
        "───────────────────────"
    ]

    if has_early:
        extra_str = format_rubles(data['extra_monthly'])
        saved_int_str = format_rubles(data['saved_interest'])
        new_over_str = format_rubles(data['new_total_overpayment'])
        saved_months = data['saved_months']
        saved_years = data['saved_years']

        lines.extend([
            f"\n🔥 <b>ЭФФЕКТ ДОСРОЧНОГО ПОГАШЕНИЯ (+{extra_str}/мес):</b>\n",
            f"⚡ <b>Срок сократится на:</b> <b>{saved_years} лет</b> (на {saved_months} мес. раньше!)",
            f"🎯 <b>Реальный срок закрытия:</b> <b>{data['actual_years']} лет</b> вместо {base['years']} лет",
            f"💰 <b>Чистая экономия на процентах:</b> <code>−{saved_int_str}</code> 🎉",
            f"📉 <b>Новая переплата банку:</b> {new_over_str} (вместо {overpayment_str})\n",
            "💡 <i>(Стратегия «Сокращение срока» сохраняет платёж прежним, но колоссально срезает итоговые проценты)</i>"
        ])
    else:
        lines.append(
            "\n💡 <i>Хотите узнать, сколько сэкономит досрочка? Нажмите кнопку с доплатой ниже!</i>"
        )

    return "\n".join(lines)


def get_loan_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Ввести свою сумму и параметры", callback_data="ln_wizard_start")
            ],
            [
                InlineKeyboardButton(text="🏠 Ипотека 6 млн (20 лет, 19%)", callback_data="ln_p_mortgage"),
            ],
            [
                InlineKeyboardButton(text="🚗 Автокредит 2.5 млн (5 лет, 18%)", callback_data="ln_p_auto"),
                InlineKeyboardButton(text="💳 Потреб 500 тыс (3 года, 22%)", callback_data="ln_p_consumer")
            ],
            [
                InlineKeyboardButton(text="🔥 Тест выгоды досрочки (+10 000 ₽/мес)", callback_data="ln_p_early_demo")
            ]
        ]
    )


def is_user_in_loan_wizard(message: types.Message) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    return user_id in user_loan_wizard


@router.message(Command("credit"))
@router.message(Command("loan"))
@router.message(Command("mortgage"))
@router.message(Command("calc_loan"))
@router.message(F.text == "🔢 Кредитный калькулятор")
async def cmd_credit_calculator(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_loan_wizard:
        del user_loan_wizard[user_id]

    text_body = message.text or ""
    # Strip command prefix
    for cmd in ["/credit", "/loan", "/mortgage", "/calc_loan", "Кредитный калькулятор"]:
        if text_body.startswith(cmd):
            text_body = text_body[len(cmd):].strip()
            break

    if text_body:
        parsed = parse_loan_query(text_body)
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
                        InlineKeyboardButton(text="✏️ Рассчитать другую сумму", callback_data="ln_wizard_start"),
                        InlineKeyboardButton(text="🔙 Меню", callback_data="ln_back_main")
                    ]
                ]
            )
            await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=kb)
            return

    intro = (
        "🔢 <b>Умный калькулятор кредитов, ипотеки и досрочных погашений</b> 💳\n\n"
        "Рассчитайте ежемесячный платёж, переплату банку и узнайте, сколько денег спасёт досрочное погашение!\n\n"
        "✍️ <b>Напишите любую вашу сумму прямо в чат:</b>\n"
        "• <code>3.5 млн 18% 5 лет</code>\n"
        "• <code>5 000 000 на 15 лет под 19.5% +15000 в месяц</code>\n"
        "• <code>800 тыс под 21% на 3 года</code>\n"
        "• <code>2000000 18 5</code> <i>(сумма ставка срок)</i>\n\n"
        "👇 <b>Или нажмите кнопку для пошагового ввода:</b>"
    )
    await message.answer(intro, parse_mode=ParseMode.HTML, reply_markup=get_loan_main_keyboard())


@router.callback_query(F.data == "ln_wizard_start")
async def callback_wizard_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_loan_wizard[user_id] = {"step": "AMOUNT"}
    text = (
        "✏️ <b>Пошаговый расчет кредита / ипотеки</b>\n\n"
        "<b>Шаг 1 из 3:</b> Отправьте в чат <b>сумму кредита</b>:\n"
        "<i>(например: <code>3 500 000</code> или <code>5 млн</code> или <code>800 тыс</code>)</i>"
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()


@router.message(F.text, is_user_in_loan_wizard)
async def handle_wizard_steps(message: types.Message):
    user_id = message.from_user.id
    wiz = user_loan_wizard.get(user_id, {})
    step = wiz.get("step")
    text = message.text.strip()

    if text.lower() in ["отмена", "стоп", "/cancel", "/exit"]:
        del user_loan_wizard[user_id]
        await message.answer("Расчет отменен.", reply_markup=get_main_menu())
        return

    # STEP 1: Amount
    if step == "AMOUNT":
        parsed = parse_loan_query(text)
        if parsed:
            amount, rate, months, extra = parsed
            wiz["amount"] = amount
            wiz["step"] = "RATE"
            await message.answer(
                f"💰 Сумма: <b>{format_rubles(amount)}</b>\n\n"
                "<b>Шаг 2 из 3:</b> Введите <b>процентную ставку</b>:\n"
                "<i>(например: <code>18.5%</code> или <code>19</code> или <code>22</code>)</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer("⚠️ Не удалось распознать сумму. Попробуйте написать, например: <code>3 000 000</code> или <code>5 млн</code>:")
        return

    # STEP 2: Rate
    if step == "RATE":
        clean_rate = text.replace("%", "").replace(",", ".").strip()
        try:
            rate_val = float(clean_rate)
            wiz["rate"] = rate_val
            wiz["step"] = "TERM"
            await message.answer(
                f"📈 Ставка: <b>{rate_val}% годовых</b>\n\n"
                "<b>Шаг 3 из 3:</b> Введите <b>срок кредита</b>:\n"
                "<i>(например: <code>5 лет</code> или <code>15 лет</code> или <code>36 месяцев</code>)</i>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await message.answer("⚠️ Введите числовую ставку (например: <code>18.5</code>):")
        return

    # STEP 3: Term
    if step == "TERM":
        parsed = parse_loan_query(f"{wiz['amount']} {wiz['rate']}% {text}")
        if parsed:
            _, _, months, _ = parsed
        else:
            try:
                num = float(text.replace("лет", "").replace("года", "").replace("год", "").strip())
                months = int(num * 12) if num <= 35 else int(num)
            except Exception:
                months = 60

        wiz["months"] = months
        amount = wiz["amount"]
        rate = wiz["rate"]
        del user_loan_wizard[user_id]

        res = calculate_annuity_loan(amount, rate, months)
        reply = format_loan_result(res)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔥 Вносить +5 000 ₽/мес досрочно", callback_data=f"ln_add_5000_{int(amount)}_{rate}_{months}"),
                    InlineKeyboardButton(text="🔥 +15 000 ₽/мес", callback_data=f"ln_add_15000_{int(amount)}_{rate}_{months}")
                ],
                [
                    InlineKeyboardButton(text="✏️ Рассчитать заново", callback_data="ln_wizard_start"),
                    InlineKeyboardButton(text="🔙 Главное меню", callback_data="ln_back_main")
                ]
            ]
        )
        await message.answer(reply, parse_mode=ParseMode.HTML, reply_markup=kb)
        return


@router.callback_query(F.data == "ln_p_mortgage")
async def callback_preset_mortgage(callback: types.CallbackQuery):
    res = calculate_annuity_loan(6_000_000, 19.0, 240)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Вносить +10 000 ₽/мес досрочно", callback_data="ln_add_10000_6000000_19.0_240"),
                InlineKeyboardButton(text="🔥 +25 000 ₽/мес", callback_data="ln_add_25000_6000000_19.0_240")
            ],
            [
                InlineKeyboardButton(text="✏️ Ввести свои данные", callback_data="ln_wizard_start"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="ln_back_main")
            ]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_p_auto")
async def callback_preset_auto(callback: types.CallbackQuery):
    res = calculate_annuity_loan(2_500_000, 18.0, 60)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Досрочно +5 000 ₽/мес", callback_data="ln_add_5000_2500000_18.0_60"),
                InlineKeyboardButton(text="🔥 +15 000 ₽/мес", callback_data="ln_add_15000_2500000_18.0_60")
            ],
            [
                InlineKeyboardButton(text="✏️ Ввести свои данные", callback_data="ln_wizard_start"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="ln_back_main")
            ]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_p_consumer")
async def callback_preset_consumer(callback: types.CallbackQuery):
    res = calculate_annuity_loan(500_000, 22.0, 36)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Досрочно +3 000 ₽/мес", callback_data="ln_add_3000_500000_22.0_36"),
                InlineKeyboardButton(text="🔥 +10 000 ₽/мес", callback_data="ln_add_10000_500000_22.0_36")
            ],
            [
                InlineKeyboardButton(text="✏️ Ввести свои данные", callback_data="ln_wizard_start"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="ln_back_main")
            ]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_p_early_demo")
async def callback_preset_early_demo(callback: types.CallbackQuery):
    res = calculate_early_repayment_savings(3_000_000, 18.5, 84, extra_monthly=10_000)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Рассчитать свои параметры", callback_data="ln_wizard_start"),
                InlineKeyboardButton(text="🔙 В меню", callback_data="ln_back_main")
            ]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("ln_add_"))
async def callback_add_extra_calc(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    extra = float(parts[2])
    amount = float(parts[3])
    rate = float(parts[4])
    months = int(parts[5])

    res = calculate_early_repayment_savings(amount, rate, months, extra_monthly=extra)
    text = format_loan_result(res)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Ввести свои параметры", callback_data="ln_wizard_start"),
                InlineKeyboardButton(text="🔙 Меню калькулятора", callback_data="ln_back_main")
            ]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_back_main")
async def callback_loan_back_main(callback: types.CallbackQuery):
    intro = (
        "🔢 <b>Умный калькулятор кредитов, ипотеки и досрочных погашений</b> 💳\n\n"
        "Рассчитайте ежемесячный платёж, переплату банку и эффект досрочных платежей!\n\n"
        "👇 <b>Выберите готовый сценарий или введите свои данные:</b>"
    )
    await callback.message.edit_text(intro, parse_mode=ParseMode.HTML, reply_markup=get_loan_main_keyboard())
    await callback.answer()
