from __future__ import annotations

from app.models.schemas import FinancialGoal, GoalProgress, UserProfile
from app.services.finance_engine import FinanceEngine
from app.services.simulator import StrategySimulator


def evaluate_goals(
    profile: UserProfile,
    monthly_investment: float,
    loan_prepayment: float,
    horizon_years: int | None = None,
) -> list[GoalProgress]:
    if not profile.financial_goals:
        return []

    engine = FinanceEngine()
    sim = StrategySimulator(engine)
    market_return = sim.market_return_for_risk(profile.risk_tolerance)
    results: list[GoalProgress] = []

    for goal in profile.financial_goals:
        years = horizon_years if horizon_years is not None else goal.target_years
        months = max(1, int(years * 12))
        projected = _project_for_goal(profile, goal, months, monthly_investment, loan_prepayment, market_return, engine)
        gap = max(0.0, goal.target_amount - projected)
        on_track = projected >= goal.target_amount * 0.95
        results.append(
            GoalProgress(
                name=goal.name,
                target_amount=goal.target_amount,
                target_years=goal.target_years,
                projected_amount=projected,
                on_track=on_track,
                gap=gap,
            )
        )
    return results


def goal_fit_score(profile: UserProfile, projected_nw: float, monthly_invest: float, loan_prepay: float) -> float:
    if not profile.financial_goals:
        return 50.0
    progress = evaluate_goals(profile, monthly_invest, loan_prepay)
    if not progress:
        return 50.0
    on_track_ratio = sum(1 for g in progress if g.on_track) / len(progress)
    avg_fill = sum(min(1.0, g.projected_amount / max(g.target_amount, 1.0)) for g in progress) / len(progress)
    return (on_track_ratio * 60.0 + avg_fill * 40.0)


def _project_for_goal(
    profile: UserProfile,
    goal: FinancialGoal,
    months: int,
    monthly_investment: float,
    loan_prepayment: float,
    market_return: float,
    engine: FinanceEngine,
) -> float:
    if goal.goal_type == "debt_free":
        debt = sum(ln.amount for ln in profile.loans)
        if debt <= 0:
            return goal.target_amount
        paid_down = loan_prepayment * months
        remaining = max(0.0, debt - paid_down)
        return goal.target_amount if remaining <= 0 else goal.target_amount - remaining

    if goal.goal_type == "savings":
        liquid = profile.savings + monthly_investment * 0.3 * months
        return liquid

    return engine.investment_growth(
        monthly_investment,
        months,
        market_return,
        initial_lump=profile.savings + sum(a.value for a in profile.assets),
    )
