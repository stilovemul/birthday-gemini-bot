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
        f"💰 <b>Сумма кредита:</b> {amount_str}",
        f"📈 <b>Процентная ставка:</b> {base['annual_rate']}% годовых",
        f"⏳ <b>Срок кредита:</b> {base['years']} лет ({base['months']} мес.)\n",
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
            f"📉 <b>Новая переплата:</b> {new_over_str} (вместо {overpayment_str})\n",
            "💡 <i>(Стратегия «Сокращение срока» сохраняет платёж прежним, но колоссально срезает итоговые проценты)</i>"
        ])
    else:
        lines.append(
            "\n💡 <i>Хотите узнать, сколько сэкономит досрочка? Добавьте к запросу «+10000» (например: <code>/credit 3 млн 18% 5 лет +10000</code>) или нажмите кнопку ниже!</i>"
        )

    return "\n".join(lines)


def get_loan_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
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


@router.message(Command("credit"))
@router.message(Command("loan"))
@router.message(Command("mortgage"))
@router.message(Command("calc_loan"))
@router.message(F.text == "🔢 Кредитный калькулятор")
async def cmd_credit_calculator(message: types.Message):
    args = (message.text or "").split(maxsplit=1)

    if len(args) > 1 and args[1].strip() and args[1].strip() != "Кредитный калькулятор":
        parsed = parse_loan_query(args[1].strip())
        if parsed:
            amount, rate, months, extra = parsed
            if extra > 0:
                res = calculate_early_repayment_savings(amount, rate, months, extra_monthly=extra)
            else:
                res = calculate_annuity_loan(amount, rate, months)

            text = format_loan_result(res)
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="➕ Посчитать с досрочкой (+5 000 ₽)", callback_data=f"ln_add_5000_{int(amount)}_{rate}_{months}"),
                        InlineKeyboardButton(text="➕ (+15 000 ₽)", callback_data=f"ln_add_15000_{int(amount)}_{rate}_{months}")
                    ],
                    [InlineKeyboardButton(text="🔙 Меню калькулятора", callback_data="ln_back_main")]
                ]
            )
            await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        else:
            await message.answer(
                "⚠️ <b>Не удалось распознать параметры.</b>\n\n"
                "<i>Примеры правильного ввода:</i>\n"
                "• <code>/credit 3000000 18% 5 лет</code>\n"
                "• <code>/credit 5 млн 19.5% 15 лет +10000</code>\n"
                "• <code>/credit 500 тыс 22% 3 года</code>",
                parse_mode=ParseMode.HTML
            )
            return

    intro = (
        "🔢 <b>Умный калькулятор кредитов, ипотеки и досрочных погашений</b> 💳\n\n"
        "Рассчитайте ежемесячный платёж, переплату банку и узнайте, сколько сотен тысяч (или миллионов) рублей вы сэкономите при даже небольшой досрочной доплате в месяц!\n\n"
        "✍️ <b>Вы можете просто написать боту в свободной форме:</b>\n"
        "• <code>/credit 5 млн 19% 15 лет</code>\n"
        "• <code>/credit 2 500 000 под 18% на 5 лет +10000 в месяц</code>\n"
        "• <code>/credit 800 тыс 21% 3 года</code>\n\n"
        "👇 <b>Или выберите готовый сценарий для быстрого расчета:</b>"
    )
    await message.answer(intro, parse_mode=ParseMode.HTML, reply_markup=get_loan_main_keyboard())


@router.callback_query(F.data == "ln_p_mortgage")
async def callback_preset_mortgage(callback: types.CallbackQuery):
    # 6 000 000 RUB, 19% rate, 20 years (240 months)
    res = calculate_annuity_loan(6_000_000, 19.0, 240)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Вносить +10 000 ₽/мес досрочно", callback_data="ln_add_10000_6000000_19.0_240"),
                InlineKeyboardButton(text="🔥 +25 000 ₽/мес", callback_data="ln_add_25000_6000000_19.0_240")
            ],
            [InlineKeyboardButton(text="🔙 Назад к пресетам", callback_data="ln_back_main")]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_p_auto")
async def callback_preset_auto(callback: types.CallbackQuery):
    # 2 500 000 RUB, 18% rate, 5 years (60 months)
    res = calculate_annuity_loan(2_500_000, 18.0, 60)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Досрочно +5 000 ₽/мес", callback_data="ln_add_5000_2500000_18.0_60"),
                InlineKeyboardButton(text="🔥 +15 000 ₽/мес", callback_data="ln_add_15000_2500000_18.0_60")
            ],
            [InlineKeyboardButton(text="🔙 Назад к пресетам", callback_data="ln_back_main")]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_p_consumer")
async def callback_preset_consumer(callback: types.CallbackQuery):
    # 500 000 RUB, 22% rate, 3 years (36 months)
    res = calculate_annuity_loan(500_000, 22.0, 36)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 Досрочно +3 000 ₽/мес", callback_data="ln_add_3000_500000_22.0_36"),
                InlineKeyboardButton(text="🔥 +10 000 ₽/мес", callback_data="ln_add_10000_500000_22.0_36")
            ],
            [InlineKeyboardButton(text="🔙 Назад к пресетам", callback_data="ln_back_main")]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_p_early_demo")
async def callback_preset_early_demo(callback: types.CallbackQuery):
    # 3 000 000 RUB, 18.5% rate, 7 years (84 months), extra 10 000 RUB/mo
    res = calculate_early_repayment_savings(3_000_000, 18.5, 84, extra_monthly=10_000)
    text = format_loan_result(res)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В меню калькулятора", callback_data="ln_back_main")]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("ln_add_"))
async def callback_add_extra_calc(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    # format: ln_add_{extra}_{amount}_{rate}_{months}
    extra = float(parts[2])
    amount = float(parts[3])
    rate = float(parts[4])
    months = int(parts[5])

    res = calculate_early_repayment_savings(amount, rate, months, extra_monthly=extra)
    text = format_loan_result(res)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В меню калькулятора", callback_data="ln_back_main")]
        ]
    )
    await callback.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ln_back_main")
async def callback_loan_back_main(callback: types.CallbackQuery):
    intro = (
        "🔢 <b>Умный калькулятор кредитов, ипотеки и досрочных погашений</b> 💳\n\n"
        "Рассчитайте ежемесячный платёж, переплату банку и эффект досрочных платежей!\n\n"
        "👇 <b>Выберите готовый сценарий:</b>"
    )
    await callback.message.edit_text(intro, parse_mode=ParseMode.HTML, reply_markup=get_loan_main_keyboard())
    await callback.answer()
