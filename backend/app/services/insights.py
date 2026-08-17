from __future__ import annotations

from app.models.schemas import (
    Assumptions,
    DebtVsInvestAdvice,
    SensitivityScenario,
    StrategyResult,
    UserProfile,
)
from app.services.finance_engine import FinanceEngine
from app.services.simulator import StrategySimulator


def debt_vs_invest_advice(profile: UserProfile, expected_return: float) -> DebtVsInvestAdvice:
    if not profile.loans:
        return DebtVsInvestAdvice(
            recommendation="invest",
            highest_loan_rate=0.0,
            expected_return=expected_return,
            rationale="No outstanding loans — focus surplus on investing and your emergency fund.",
        )
    highest = max(ln.interest_rate for ln in profile.loans)
    spread = highest - expected_return
    if spread > 2.0:
        rec = "prepay_debt"
        rationale = (
            f"Your highest loan rate ({highest:.1f}%) exceeds expected investment returns "
            f"({expected_return:.1f}%) by {spread:.1f}pp — prepaying debt is likely the better use of surplus."
        )
    elif spread < -1.0:
        rec = "invest"
        rationale = (
            f"Expected returns ({expected_return:.1f}%) exceed your highest loan rate ({highest:.1f}%) — "
            "investing surplus while paying EMIs on schedule may build more wealth."
        )
    else:
        rec = "balanced"
        rationale = (
            f"Loan rates ({highest:.1f}%) and expected returns ({expected_return:.1f}%) are close — "
            "a balanced split between investing and extra loan paydown is sensible."
        )
    return DebtVsInvestAdvice(
        recommendation=rec,
        highest_loan_rate=highest,
        expected_return=expected_return,
        rationale=rationale,
    )


def build_assumptions(profile: UserProfile, horizon_years: int, ef_months: float) -> Assumptions:
    sim = StrategySimulator()
    return Assumptions(
        horizon_years=horizon_years,
        market_return_pct=sim.market_return_for_risk(profile.risk_tolerance),
        emergency_fund_months=ef_months,
        inflation_pct=5.0,
        tax_included=False,
    )


def build_next_actions(
    profile: UserProfile,
    best: StrategyResult,
    loan_order: list[str],
    ef_target: float,
    debt_advice: DebtVsInvestAdvice,
) -> list[str]:
    actions: list[str] = []
    ef_gap = max(0.0, ef_target - profile.savings)
    if ef_gap > 0:
        actions.append(
            f"Build emergency fund to ₹{ef_target:,.0f} (currently ₹{profile.savings:,.0f}; short by ₹{ef_gap:,.0f})."
        )
    elif profile.savings >= ef_target:
        actions.append(f"Emergency fund target met (₹{ef_target:,.0f}). Consider redirecting surplus to goals.")

    if loan_order and best.loan_prepayment_monthly > 0:
        actions.append(
            f"Prepay ₹{best.loan_prepayment_monthly:,.0f}/month toward **{loan_order[0]}** (highest-rate loan first)."
        )
    elif debt_advice.recommendation == "prepay_debt" and loan_order:
        actions.append(f"Prioritize closing **{loan_order[0]}** before increasing investments.")

    if best.monthly_investment_suggested > 0:
        actions.append(
            f"Start or increase monthly investments by ₹{best.monthly_investment_suggested:,.0f} "
            f"using the **{best.name.replace('_', ' ')}** strategy."
        )

    if profile.financial_goals:
        behind = [g.name for g in profile.financial_goals]
        actions.append(f"Track progress toward goals: {', '.join(behind[:3])}.")

    return actions[:3]


def sensitivity_analysis(
    profile: UserProfile,
    monthly_invest: float,
    loan_prepay: float,
    horizon_years: int,
    base_return: float,
) -> list[SensitivityScenario]:
    engine = FinanceEngine()
    months = horizon_years * 12
    scenarios = [
        ("Optimistic", base_return + 2.0),
        ("Base case", base_return),
        ("Pessimistic", max(0.0, base_return - 3.0)),
    ]
    return [
        SensitivityScenario(
            label=label,
            return_pct=ret,
            projected_net_worth=engine.net_worth_projection(
                profile, months, monthly_invest, loan_prepay, ret
            ),
        )
        for label, ret in scenarios
    ]
