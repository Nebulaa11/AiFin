from app.models.schemas import LoanItem, UserProfile
from app.services.local_agent import LocalFinanceAgent


def test_greeting_intent():
    agent = LocalFinanceAgent()
    profile = UserProfile(
        age=28,
        income_monthly=80000,
        expenses_monthly=40000,
        savings=200000,
        loans=[LoanItem(name="car", amount=500000, interest_rate=10, emi=12000)],
    )
    answer = agent.answer(profile, "hey", user_name="Vivek")
    assert "Vivek" in answer or "Hey" in answer
    assert "₹" in answer


def test_debt_intent():
    agent = LocalFinanceAgent()
    profile = UserProfile(
        age=30,
        income_monthly=100000,
        expenses_monthly=50000,
        savings=100000,
        loans=[LoanItem(name="home", amount=2000000, interest_rate=9, emi=25000)],
    )
    answer = agent.answer(profile, "which loan should I pay first")
    assert "home" in answer.lower() or "9" in answer


def test_predict_intent():
    agent = LocalFinanceAgent()
    agent._ensure_model()
    assert agent.predict_intent("hello there") == "greeting"
    assert agent.predict_intent("emergency fund target") == "emergency_fund"
