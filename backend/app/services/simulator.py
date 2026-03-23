from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import UserProfile
from app.services.finance_engine import FinanceEngine


@dataclass
class SimulationOutcome:
    horizon_months: int
    net_worth_end: float
    path_net_worth: list[float]


class StrategySimulator:
    def __init__(self, engine: FinanceEngine | None = None):
        self.engine = engine or FinanceEngine()

    def market_return_for_risk(self, risk: str) -> float:
        mapping = {"low": 6.5, "medium": 9.0, "high": 11.5}
        return mapping.get(risk, 9.0)

    def simulate_years(
        self,
        profile: UserProfile,
        years: int,
        monthly_investment: float,
        loan_prepayment_monthly: float,
    ) -> SimulationOutcome:
        months = years * 12
        mret = self.market_return_for_risk(profile.risk_tolerance)
        nw = self.engine.net_worth_projection(
            profile,
            months,
            monthly_investment,
            loan_prepayment_monthly,
            mret,
        )
        path = []
        step = max(1, months // 24)
        for m in range(0, months + 1, step):
            path.append(
                self.engine.net_worth_projection(
                    profile,
                    m,
                    monthly_investment,
                    loan_prepayment_monthly,
                    mret,
                )
            )
        return SimulationOutcome(horizon_months=months, net_worth_end=nw, path_net_worth=path)
