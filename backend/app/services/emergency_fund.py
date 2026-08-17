from __future__ import annotations

from app.models.schemas import UserProfile


def emergency_fund_months(profile: UserProfile) -> float:
    """Dynamic emergency fund rule based on profile risk factors."""
    months = 6.0
    total_debt = sum(ln.amount for ln in profile.loans)
    debt_to_income = total_debt / max(profile.income_monthly * 12, 1.0)
    if debt_to_income > 0.5:
        months += 2.0
    elif debt_to_income > 0.25:
        months += 1.0
    if profile.risk_tolerance == "low":
        months += 1.0
    months += min(profile.dependents, 3) * 0.5
    coverage = profile.savings / max(profile.expenses_monthly, 1.0)
    if coverage >= 9:
        months -= 1.0
    return max(3.0, min(12.0, months))


def emergency_fund_target(profile: UserProfile) -> tuple[float, float]:
    months = emergency_fund_months(profile)
    return profile.expenses_monthly * months, months
