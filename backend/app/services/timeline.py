from __future__ import annotations

from app.models.schemas import TimelinePoint, UserProfile
from app.services.finance_engine import FinanceEngine


def build_timeline(
    profile: UserProfile,
    months: int,
    monthly_invest: float,
    loan_extra: float,
    market_return_pct: float,
    lump_sum_prepayment: float = 0.0,
) -> list[TimelinePoint]:
    engine = FinanceEngine()
    r_m = market_return_pct / 12.0 / 100.0
    invest_balance = profile.savings
    loan_state = [(ln.amount, ln.interest_rate, ln.emi) for ln in profile.loans]
    if lump_sum_prepayment > 0 and loan_state:
        idx = max(range(len(loan_state)), key=lambda i: loan_state[i][1])
        bal, rate, emi = loan_state[idx]
        loan_state[idx] = (max(0.0, bal - lump_sum_prepayment), rate, emi)
    asset_val = sum(a.value for a in profile.assets)
    monthly_surplus = profile.income_monthly - profile.expenses_monthly
    invest_flow = min(monthly_invest, max(0.0, monthly_surplus - loan_extra))

    points: list[TimelinePoint] = []
    step = max(1, months // 24)

    for m in range(0, months + 1):
        if m > 0:
            invest_balance = invest_balance * (1 + r_m) + invest_flow
            pay_extra = loan_extra / max(1, len(loan_state)) if loan_state else 0
            for i, (bal, rate, emi) in enumerate(loan_state):
                if bal <= 0:
                    continue
                rr = rate / 12.0 / 100.0
                interest = bal * rr
                princ = emi - interest + (pay_extra if i == 0 else 0)
                loan_state[i] = (max(0.0, bal - princ), rate, emi)
            asset_val = asset_val * (1 + r_m / 12.0)

        total_debt = sum(max(0.0, b[0]) for b in loan_state)
        nw = invest_balance + asset_val - total_debt
        if m % step == 0 or m == months:
            points.append(
                TimelinePoint(
                    month=m,
                    net_worth=nw,
                    investments=invest_balance + asset_val,
                    total_debt=total_debt,
                    liquid_savings=invest_balance,
                )
            )
    return points
