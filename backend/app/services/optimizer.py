from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import StrategyResult, UserProfile
from app.services.finance_engine import FinanceEngine
from app.services.simulator import StrategySimulator


@dataclass
class StrategySpec:
    name: str
    description: str
    monthly_investment: float
    loan_prepayment_monthly: float


class OptimizationEngine:
    def __init__(self):
        self.engine = FinanceEngine()
        self.sim = StrategySimulator(self.engine)

    def loan_repayment_order(self, profile: UserProfile) -> list[str]:
        loans = sorted(profile.loans, key=lambda x: x.interest_rate, reverse=True)
        return [ln.name for ln in loans]

    def _surplus(self, profile: UserProfile) -> float:
        return max(0.0, profile.income_monthly - profile.expenses_monthly)

    def build_strategies(self, profile: UserProfile) -> list[StrategySpec]:
        s = self._surplus(profile)
        if s <= 0:
            return [
                StrategySpec(
                    "survival_min_invest",
                    "No surplus: minimize investment, focus on mandatory obligations.",
                    0.0,
                    0.0,
                )
            ]

        return [
            StrategySpec(
                "repay_loans_aggressive",
                "Allocate most surplus to extra loan principal.",
                s * 0.1,
                s * 0.7,
            ),
            StrategySpec(
                "invest_aggressive",
                "Maximize monthly investments; minimum extra loan paydown.",
                s * 0.65,
                s * 0.05,
            ),
            StrategySpec(
                "balanced",
                "Split surplus between investing and debt reduction.",
                s * 0.35,
                s * 0.35,
            ),
            StrategySpec(
                "emergency_first",
                "Build liquid buffer before heavy investing.",
                s * 0.25,
                s * 0.25,
            ),
        ]

    def _risk_score(self, profile: UserProfile, spec: StrategySpec, nw: float) -> float:
        avg_loan = (
            sum(l.interest_rate for l in profile.loans) / len(profile.loans) if profile.loans else 0
        )
        invest_ratio = spec.monthly_investment / max(self._surplus(profile), 1e-6)
        base = min(100.0, avg_loan * 2.0 + invest_ratio * 40.0)
        if profile.risk_tolerance == "low":
            base *= 0.85
        elif profile.risk_tolerance == "high":
            base *= 1.1
        return min(100.0, base)

    def _stability(self, profile: UserProfile, spec: StrategySpec) -> float:
        months_cov = profile.savings / max(profile.expenses_monthly, 1.0)
        prep = spec.loan_prepayment_monthly
        return min(100.0, months_cov * 8.0 + prep / max(profile.income_monthly, 1.0) * 30.0)

    def _composite(self, nw: float, risk: float, stability: float) -> float:
        return nw * 1.0 - risk * 500.0 + stability * 200.0

    def evaluate(self, profile: UserProfile, horizon_years: int = 10) -> list[StrategyResult]:
        specs = self.build_strategies(profile)
        results: list[StrategyResult] = []
        for sp in specs:
            out = self.sim.simulate_years(profile, horizon_years, sp.monthly_investment, sp.loan_prepayment_monthly)
            nw = out.net_worth_end
            risk = self._risk_score(profile, sp, nw)
            stab = self._stability(profile, sp)
            comp = self._composite(nw, risk, stab)
            results.append(
                StrategyResult(
                    name=sp.name,
                    description=sp.description,
                    future_net_worth=nw,
                    risk_score=risk,
                    cash_flow_stability=stab,
                    composite_score=comp,
                    monthly_investment_suggested=sp.monthly_investment,
                    loan_prepayment_monthly=sp.loan_prepayment_monthly,
                )
            )
        results.sort(key=lambda r: r.composite_score, reverse=True)
        return results
