import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("LoanCalculator")


def calculate_annuity_loan(amount: float, annual_rate: float, months: int) -> Dict[str, Any]:
    """
    Calculates standard annuity loan details.
    amount: Principal loan amount in RUB
    annual_rate: Annual interest rate in percent (e.g. 18.5 for 18.5%)
    months: Total duration in months
    """
    if amount <= 0 or months <= 0:
        return {}

    if annual_rate <= 0:
        monthly_payment = amount / months
        total_payout = amount
        total_overpayment = 0.0
    else:
        monthly_rate = (annual_rate / 100.0) / 12.0
        # Annuity formula: A = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
        annuity_factor = (monthly_rate * ((1 + monthly_rate) ** months)) / (((1 + monthly_rate) ** months) - 1)
        monthly_payment = amount * annuity_factor
        total_payout = monthly_payment * months
        total_overpayment = total_payout - amount

    return {
        "amount": amount,
        "annual_rate": annual_rate,
        "months": months,
        "years": round(months / 12, 1),
        "monthly_payment": round(monthly_payment),
        "total_payout": round(total_payout),
        "total_overpayment": round(total_overpayment),
        "overpayment_percent": round((total_overpayment / amount) * 100, 1)
    }


def calculate_early_repayment_savings(
    amount: float,
    annual_rate: float,
    months: int,
    extra_monthly: float = 0.0,
    one_time_extra: float = 0.0,
    one_time_month: int = 1
) -> Dict[str, Any]:
    """
    Simulates loan amortization with early repayments (month-by-month schedule)
    with the 'Reduce Loan Term' strategy (saves the most money).
    """
    base = calculate_annuity_loan(amount, annual_rate, months)
    if not base or (extra_monthly <= 0 and one_time_extra <= 0):
        return {"base": base, "has_early": False}

    monthly_rate = (annual_rate / 100.0) / 12.0 if annual_rate > 0 else 0
    base_payment = base["monthly_payment"]

    balance = amount
    total_interest_paid = 0.0
    actual_months = 0

    while balance > 0.01 and actual_months < months + 120:
        actual_months += 1
        interest_for_month = balance * monthly_rate
        total_interest_paid += interest_for_month

        # Regular principal reduction
        regular_principal = base_payment - interest_for_month
        if regular_principal < 0:
            regular_principal = 0

        # Prepayment addition
        extra_this_month = extra_monthly
        if actual_months == one_time_month:
            extra_this_month += one_time_extra

        total_principal_payment = regular_principal + extra_this_month

        if total_principal_payment >= balance:
            balance = 0
            break
        else:
            balance -= total_principal_payment

    saved_interest = max(0.0, base["total_overpayment"] - total_interest_paid)
    saved_months = max(0, months - actual_months)
    saved_years = round(saved_months / 12, 1)

    return {
        "base": base,
        "has_early": True,
        "extra_monthly": extra_monthly,
        "one_time_extra": one_time_extra,
        "actual_months": actual_months,
        "actual_years": round(actual_months / 12, 1),
        "saved_months": saved_months,
        "saved_years": saved_years,
        "new_total_overpayment": round(total_interest_paid),
        "new_total_payout": round(amount + total_interest_paid),
        "saved_interest": round(saved_interest),
        "saved_interest_percent": round((saved_interest / base["total_overpayment"]) * 100, 1) if base["total_overpayment"] > 0 else 0
    }


def parse_loan_query(text: str) -> Optional[Tuple[float, float, int, float]]:
    """
    Parses strings like:
    - '3000000 18% 5y'
    - '5 млн 20% 15 лет'
    - '1 500 000 под 19.5% на 3 года досрочно 10000'
    - '500k 22% 2 года'
    Returns: (amount, annual_rate, months, extra_monthly)
    """
    raw = text.lower().replace(" ", "").replace(",", ".").replace("₽", "").replace("руб", "")

    # Extract Amount
    amount = 0.0
    # Match millions: e.g. 5млн, 3.5млн, 5m
    m_mln = re.search(r"(\d+(?:\.\d+)?)(?:млн|m|kk)", raw)
    if m_mln:
        amount = float(m_mln.group(1)) * 1_000_000
    else:
        # Match thousands: e.g. 500k, 500тыс
        m_k = re.search(r"(\d+(?:\.\d+)?)(?:k|тыс)", raw)
        if m_k:
            amount = float(m_k.group(1)) * 1_000
        else:
            # Match plain large number: e.g. 3000000
            m_plain = re.search(r"(?:^|[^\d%.])(\d{4,9})(?:[^\d%]|$)", raw)
            if m_plain:
                amount = float(m_plain.group(1))

    # Extract Rate (e.g. 18.5%, 20%, под19%)
    rate = 0.0
    m_rate = re.search(r"(\d+(?:\.\d+)?)\s*%", raw)
    if not m_rate:
        m_rate = re.search(r"под(\d+(?:\.\d+)?)", raw)
    if m_rate:
        rate = float(m_rate.group(1))
    else:
        rate = 19.0  # Default current market rate benchmark if omitted

    # Extract Duration (Years / Months)
    months = 0
    m_years = re.search(r"(\d+)(?:y|г|лет|года|год)", raw)
    if m_years:
        months = int(m_years.group(1)) * 12
    else:
        m_months = re.search(r"(\d+)(?:m|мес|месяцев|месяца)", raw)
        if m_months:
            months = int(m_months.group(1))
        else:
            months = 60  # Default 5 years

    # Extract Extra Monthly Prepayment (e.g. досрочно 10000, +5000, доплата 15k)
    extra = 0.0
    m_extra = re.search(r"(?:\+|досрочно|доплата|сверху)(\d+(?:\.\d+)?)(?:k|тыс)?", raw)
    if m_extra:
        val = float(m_extra.group(1))
        if "k" in m_extra.group(0) or "тыс" in m_extra.group(0):
            val *= 1000
        extra = val

    if amount > 1000:
        return amount, rate, months, extra
    return None
