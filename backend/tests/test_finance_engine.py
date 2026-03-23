from app.models.schemas import LoanItem, UserProfile
from app.services.finance_engine import FinanceEngine


def test_emi():
    fe = FinanceEngine()
    emi = fe.calculate_emi(500_000, 10, 60)
    assert 10_000 < emi < 12_000


def test_net_worth_projection():
    fe = FinanceEngine()
    p = UserProfile(
        age=28,
        income_monthly=80_000,
        expenses_monthly=40_000,
        savings=200_000,
        loans=[LoanItem(name="car", amount=500_000, interest_rate=10, emi=12_000)],
    )
    nw = fe.net_worth_projection(p, months=120, monthly_invest=10_000, loan_extra_paydown=5_000, market_return_pct=9.0)
    assert nw > 0
