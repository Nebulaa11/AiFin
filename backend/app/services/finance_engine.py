from __future__ import annotations

import math
from dataclasses import dataclass

from app.models.schemas import UserProfile


@dataclass
class LoanMetrics:
    name: str
    principal: float
    annual_rate_pct: float
    emi: float
    months_remaining: int
    remaining_interest_total: float


class FinanceEngine:
    @staticmethod
    def calculate_emi(principal: float, annual_rate_pct: float, months: int) -> float:
        if months <= 0:
            return 0.0
        if annual_rate_pct <= 0:
            return principal / months
        r = annual_rate_pct / 12.0 / 100.0
        return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)

    @staticmethod
    def months_to_payoff(principal: float, emi: float, annual_rate_pct: float) -> int:
        if emi <= 0 or principal <= 0:
            return 999 * 12
        if annual_rate_pct <= 0:
            return int(math.ceil(principal / emi))
        r = annual_rate_pct / 12.0 / 100.0
        denom = emi - r * principal
        if denom <= 0:
            return 999 * 12
        n = math.log(emi / denom) / math.log(1 + r)
        return max(1, int(math.ceil(n)))

    @staticmethod
    def loan_remaining_interest(
        principal: float,
        annual_rate_pct: float,
        emi: float,
        months_paid: int = 0,
    ) -> float:
        if principal <= 0:
            return 0.0
        r = annual_rate_pct / 12.0 / 100.0
        balance = principal
        total_interest = 0.0
        for _ in range(months_paid):
            interest = balance * r
            principal_part = emi - interest
            total_interest += interest
            balance = max(0.0, balance - principal_part)
        while balance > 0.01 and total_interest < 1e12:
            interest = balance * r
            principal_part = emi - interest
            if principal_part <= 0:
                return float("inf")
            total_interest += interest
            balance -= principal_part
        return total_interest

    @staticmethod
    def investment_growth(
        monthly_contribution: float,
        months: int,
        annual_return_pct: float,
        initial_lump: float = 0.0,
    ) -> float:
        if months <= 0:
            return initial_lump
        r_m = annual_return_pct / 12.0 / 100.0
        if abs(r_m) < 1e-12:
            return initial_lump + monthly_contribution * months
        fv_lump = initial_lump * (1 + r_m) ** months
        fv_series = monthly_contribution * (((1 + r_m) ** months - 1) / r_m)
        return fv_lump + fv_series

    @staticmethod
    def net_worth_projection(
        profile: UserProfile,
        months: int,
        monthly_invest: float,
        loan_extra_paydown: float,
        market_return_pct: float,
    ) -> float:
        cash = profile.savings
        total_invest = cash
        monthly_surplus = profile.income_monthly - profile.expenses_monthly
        invest_flow = min(monthly_invest, max(0.0, monthly_surplus - loan_extra_paydown))
        loan_state = [(ln.amount, ln.interest_rate, ln.emi, ln.name) for ln in profile.loans]
        asset_val = sum(a.value for a in profile.assets)
        r_m = market_return_pct / 12.0 / 100.0

        for _ in range(months):
            total_invest = total_invest * (1 + r_m) + invest_flow
            pay_extra = loan_extra_paydown / max(1, len(loan_state)) if loan_state else 0
            for i, (bal, rate, emi, _) in enumerate(loan_state):
                if bal <= 0:
                    continue
                rr = rate / 12.0 / 100.0
                interest = bal * rr
                princ = emi - interest + (pay_extra if i == 0 else 0)
                bal = max(0.0, bal - princ)
                loan_state[i] = (bal, rate, emi, loan_state[i][3])
            asset_val = asset_val * (1 + r_m / 12.0)

        debt = sum(max(0.0, b[0]) for b in loan_state)
        return total_invest + asset_val - debt

    def profile_metrics(self, profile: UserProfile) -> dict:
        loans: list[LoanMetrics] = []
        for ln in profile.loans:
            months_left = self.months_to_payoff(ln.amount, ln.emi, ln.interest_rate)
            rem_int = self.loan_remaining_interest(ln.amount, ln.interest_rate, ln.emi, 0)
            loans.append(
                LoanMetrics(
                    name=ln.name,
                    principal=ln.amount,
                    annual_rate_pct=ln.interest_rate,
                    emi=ln.emi,
                    months_remaining=months_left,
                    remaining_interest_total=rem_int if math.isfinite(rem_int) else 0.0,
                )
            )
        monthly_free = profile.income_monthly - profile.expenses_monthly
        return {
            "monthly_surplus": monthly_free,
            "months_of_expenses_in_savings": profile.savings / max(profile.expenses_monthly, 1.0),
            "loans": loans,
            "total_assets": sum(a.value for a in profile.assets),
        }
