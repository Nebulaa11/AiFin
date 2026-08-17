from app.models.schemas import FinancialGoal, LoanItem, UserProfile
from app.services.emergency_fund import emergency_fund_months, emergency_fund_target
from app.services.goal_planner import goal_fit_score
from app.services.insights import debt_vs_invest_advice


def test_emergency_fund_dynamic():
    profile = UserProfile(
        age=28,
        income_monthly=80_000,
        expenses_monthly=40_000,
        savings=200_000,
        loans=[LoanItem(name="car", amount=500_000, interest_rate=10, emi=12_000)],
        dependents=2,
        risk_tolerance="low",
    )
    months = emergency_fund_months(profile)
    assert months >= 6.0
    target, _ = emergency_fund_target(profile)
    assert target == profile.expenses_monthly * months


def test_debt_vs_invest():
    profile = UserProfile(
        age=30,
        income_monthly=100_000,
        expenses_monthly=50_000,
        savings=100_000,
        loans=[LoanItem(name="personal", amount=200_000, interest_rate=14, emi=8000)],
    )
    advice = debt_vs_invest_advice(profile, expected_return=9.0)
    assert advice.recommendation == "prepay_debt"


def test_goal_fit_with_no_goals():
    profile = UserProfile(
        age=28,
        income_monthly=80_000,
        expenses_monthly=40_000,
        savings=200_000,
    )
    score = goal_fit_score(profile, 1_000_000, 10_000, 5_000)
    assert score == 50.0


def test_goal_fit_with_goals():
    profile = UserProfile(
        age=28,
        income_monthly=80_000,
        expenses_monthly=40_000,
        savings=200_000,
        financial_goals=[
            FinancialGoal(name="retire", target_amount=500_000, target_years=5, goal_type="investment")
        ],
    )
    score = goal_fit_score(profile, 2_000_000, 15_000, 5_000)
    assert 0 <= score <= 100
