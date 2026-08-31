import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("LoanCalculator")


def calculate_annuity_loan(amount: float, annual_rate: float, months: int) -> Dict[str, Any]:
    """
    Calculates standard annuity loan details.
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
        "overpayment_percent": round((total_overpayment / amount) * 100, 1) if amount > 0 else 0
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
    Simulates loan amortization with early repayments (month-by-month schedule).
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

        regular_principal = base_payment - interest_for_month
        if regular_principal < 0:
            regular_principal = 0

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
    Super flexible parser for loan queries in Russian and numerical formats:
    - '3000000 18% 5y'
    - '3500000 19 5'
    - '5 млн 20% 15 лет'
    - '3.5 миллиона под 18.5 на 5 лет досрочно 10000'
    - '500 тыс на 3 года под 22%'
    - '2 000 000 18'
    """
    clean = text.lower().replace("₽", "").replace("руб", "").replace("рублей", "").strip()
    
    # 1. Check for millions/thousands keywords
    amount = 0.0
    m_mln = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:млн|миллион|миллиона|миллионов|m|kk)", clean)
    if m_mln:
        amount = float(m_mln.group(1).replace(",", ".")) * 1_000_000
    else:
        m_ths = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:тыс|тысяч|тысячи|k)", clean)
        if m_ths:
            amount = float(m_ths.group(1).replace(",", ".")) * 1_000
        else:
            # Look for sequence of digits (e.g. 3 500 000 or 3500000)
            digits_match = re.search(r"(\d[\d\s.,]{3,12}\d)", clean)
            if digits_match:
                cand = re.sub(r"[\s_]", "", digits_match.group(1)).replace(",", ".")
                try:
                    cand_f = float(cand)
                    if cand_f >= 1000:
                        amount = cand_f
                except Exception:
                    pass

    # 2. Check for rate (e.g. 18.5%, под 19%, 19.5)
    rate = 0.0
    m_rate = re.search(r"(\d+(?:[.,]\d+)?)\s*%", clean)
    if not m_rate:
        m_rate = re.search(r"(?:под|ставка)\s*(\d+(?:[.,]\d+)?)", clean)
    if m_rate:
        rate = float(m_rate.group(1).replace(",", "."))

    # 3. Check for duration (years / months)
    months = 0
    m_yr = re.search(r"(\d+)\s*(?:лет|года|год|y|г)", clean)
    if m_yr:
        months = int(m_yr.group(1)) * 12
    else:
        m_mo = re.search(r"(\d+)\s*(?:мес|месяцев|месяца|m)", clean)
        if m_mo:
            months = int(m_mo.group(1))

    # 4. Check for extra prepayment
    extra = 0.0
    m_extra = re.search(r"(?:\+|досрочно|доплата|сверху|плюс)\s*(\d+(?:[.,]\d+)?)\s*(?:k|тыс|млн)?", clean)
    if m_extra:
        val = float(m_extra.group(1).replace(",", "."))
        matched_str = m_extra.group(0)
        if "млн" in matched_str:
            val *= 1_000_000
        elif "k" in matched_str or "тыс" in matched_str:
            val *= 1_000
        extra = val

    # 5. If amount found but rate or months omitted, check positional numbers (e.g. '3500000 18 5')
    if amount > 0 and (rate <= 0 or months <= 0):
        # Find all isolated numbers
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", clean)
        num_floats = []
        for n in numbers:
            try:
                num_floats.append(float(n.replace(",", ".")))
            except Exception:
                pass
        
        # Remove the amount number
        remaining = [n for n in num_floats if abs(n - amount) > 1 and abs(n - (amount / 1000000)) > 0.01 and abs(n - (amount / 1000)) > 0.01]
        
        if rate <= 0 and remaining:
            # Rates are usually 5.0 to 45.0
            rate_cand = next((n for n in remaining if 1.0 <= n <= 50.0), None)
            if rate_cand:
                rate = rate_cand
                remaining.remove(rate_cand)

        if months <= 0 and remaining:
            # Term is usually 1 to 30 years or 6 to 360 months
            term_cand = remaining[0]
            if term_cand <= 30:
                months = int(term_cand * 12)
            else:
                months = int(term_cand)

    # Defaults if user only entered amount (e.g. '/credit 3500000')
    if amount >= 1000:
        if rate <= 0:
            rate = 19.0  # standard market benchmark
        if months <= 0:
            months = 60  # standard 5 years default
        return amount, rate, months, extra

    return None
