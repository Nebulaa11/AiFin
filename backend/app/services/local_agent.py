from __future__ import annotations

import json
import re
from pathlib import Path

import joblib

from app.models.schemas import UserProfile
from app.services.emergency_fund import emergency_fund_target
from app.services.finance_engine import FinanceEngine
from app.services.insights import debt_vs_invest_advice
from app.services.optimizer import OptimizationEngine
from app.services.simulator import StrategySimulator

KEYWORD_INTENTS: list[tuple[str, str]] = [
    (r"\b(hi|hey|hello|sup|morning|help)\b", "greeting"),
    (r"\b(loan|debt|emi|payoff|prepay)\b", "debt_payoff"),
    (r"\b(invest.*debt|debt.*invest|vs|or pay)\b", "debt_vs_invest"),
    (r"\b(emergency|buffer|rainy)\b", "emergency_fund"),
    (r"\b(sip|invest|mutual|monthly.*invest)\b", "sip_advice"),
    (r"\b(strategy|plan|optimize|balanced|aggressive)\b", "strategy_advice"),
    (r"\b(goal|track|house|retire)\b", "goal_advice"),
    (r"\b(net worth|summary|how am i|assets|total debt)\b", "net_worth"),
]


class LocalFinanceAgent:
    """Free on-device finance coach using a trained intent model + profile-aware templates."""

    def __init__(self):
        self.engine = FinanceEngine()
        self.optimizer = OptimizationEngine()
        self.sim = StrategySimulator(self.engine)
        self._pipe = None
        self._loaded = False
        self.model_dir = Path(__file__).resolve().parent.parent.parent / "models_saved"

    def _ensure_model(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        model_path = self.model_dir / "chat_intent_classifier.joblib"
        if model_path.is_file():
            try:
                self._pipe = joblib.load(model_path)
                return
            except Exception:
                self._pipe = None
        self._auto_train()

    def _auto_train(self) -> None:
        from app.ml.chat_training import train_chat_intent_classifier

        csv_path = self.model_dir.parent.parent / "data" / "chat_intent_training.csv"
        if not csv_path.is_file():
            return
        try:
            train_chat_intent_classifier(csv_path, model_dir=self.model_dir)
            self._pipe = joblib.load(self.model_dir / "chat_intent_classifier.joblib")
        except Exception:
            self._pipe = None

    def predict_intent(self, question: str) -> str:
        q = question.strip().lower()
        for pattern, intent in KEYWORD_INTENTS:
            if re.search(pattern, q):
                return intent
        self._ensure_model()
        if self._pipe is not None:
            try:
                return str(self._pipe.predict([q])[0])
            except Exception:
                pass
        return "general"

    def answer(
        self,
        profile: UserProfile | None,
        question: str,
        history: list[dict] | None = None,
        user_name: str = "there",
        analysis: dict | None = None,
    ) -> str:
        if not profile:
            return (
                "Hi! I'm your AiFin coach (free local model). "
                "Fill in your profile under Assets and Debts, then ask me about loans, "
                "investing, emergency funds, or your strategy."
            )

        intent = self.predict_intent(question)
        first = user_name.split()[0] if user_name else "there"

        handlers = {
            "greeting": self._greeting,
            "debt_payoff": self._debt_payoff,
            "debt_vs_invest": self._debt_vs_invest,
            "emergency_fund": self._emergency_fund,
            "sip_advice": self._sip_advice,
            "strategy_advice": self._strategy_advice,
            "goal_advice": self._goal_advice,
            "net_worth": self._net_worth,
            "general": self._general,
        }
        handler = handlers.get(intent, self._general)
        return handler(profile, first, analysis)

    def _fmt(self, n: float) -> str:
        return f"₹{n:,.0f}"

    def _surplus(self, profile: UserProfile) -> float:
        return max(0.0, profile.income_monthly - profile.expenses_monthly)

    def _best_from_analysis(self, analysis: dict | None) -> dict | None:
        if not analysis:
            return None
        name = analysis.get("best_strategy_name")
        for s in analysis.get("strategies", []):
            if s.get("name") == name:
                return s
        return None

    def _greeting(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        debt = sum(l.amount for l in profile.loans)
        surplus = self._surplus(profile)
        lines = [
            f"Hey {first}! I'm AiFin — your free local finance coach (no API costs).",
            "",
            f"Quick snapshot: income {self._fmt(profile.income_monthly)}/mo, "
            f"expenses {self._fmt(profile.expenses_monthly)}/mo, "
            f"savings {self._fmt(profile.savings)}, debt {self._fmt(debt)}.",
        ]
        if surplus > 0:
            lines.append(f"Monthly surplus: about {self._fmt(surplus)}.")
        lines.append("")
        lines.append(
            "Ask me about debt payoff, SIP amounts, emergency fund, strategy, or your goals — "
            "I'll use your actual numbers."
        )
        if analysis:
            lines.append(
                f"\nLatest plan favours **{analysis.get('best_strategy_name', '').replace('_', ' ')}**."
            )
        return "\n".join(lines)

    def _debt_payoff(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        if not profile.loans:
            return f"{first}, you have no loans on file — focus on building your emergency fund and investing your surplus."
        order = self.optimizer.loan_repayment_order(profile)
        top = max(profile.loans, key=lambda x: x.interest_rate)
        best = self._best_from_analysis(analysis)
        prepay = best.get("loan_prepayment_monthly", 0) if best else self._surplus(profile) * 0.35
        return (
            f"{first}, attack **{order[0]}** first (highest rate: {top.interest_rate}% p.a.).\n\n"
            f"Suggested extra prepayment: **{self._fmt(prepay)}/month** on top of EMIs. "
            f"Payoff priority: {' → '.join(order)}.\n\n"
            "Avalanche method (highest rate first) saves the most interest over time."
        )

    def _debt_vs_invest(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        ret = self.sim.market_return_for_risk(profile.risk_tolerance)
        advice = debt_vs_invest_advice(profile, ret)
        if analysis and analysis.get("debt_vs_invest"):
            advice_text = analysis["debt_vs_invest"].get("rationale", advice.rationale)
        else:
            advice_text = advice.rationale
        return f"{first}, here's the debt-vs-invest view:\n\n{advice_text}"

    def _emergency_fund(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        target, months = emergency_fund_target(profile)
        gap = max(0.0, target - profile.savings)
        if analysis:
            target = analysis.get("emergency_fund_target", target)
            months = analysis.get("emergency_fund_months", months)
            gap = max(0.0, target - profile.savings)
        if gap <= 0:
            return (
                f"{first}, your emergency fund looks healthy — "
                f"target {self._fmt(target)} ({months:.1f} months of expenses) and you have {self._fmt(profile.savings)}."
            )
        return (
            f"{first}, aim for **{self._fmt(target)}** in liquid savings "
            f"({months:.1f} months of expenses). You're at {self._fmt(profile.savings)} — "
            f"short by **{self._fmt(gap)}**. Build this before aggressive investing."
        )

    def _sip_advice(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        best = self._best_from_analysis(analysis)
        if best:
            sip = best.get("monthly_investment_suggested", 0)
        else:
            strategies = self.optimizer.evaluate(profile, horizon_years=10)
            sip = strategies[0].monthly_investment_suggested if strategies else 0
        surplus = self._surplus(profile)
        return (
            f"{first}, with {self._fmt(surplus)}/month surplus, "
            f"a disciplined SIP of **{self._fmt(sip)}/month** fits your profile "
            f"({profile.risk_tolerance} risk tolerance).\n\n"
            "Keep EMIs on schedule and maintain your emergency fund before increasing SIP."
        )

    def _strategy_advice(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        if analysis:
            name = analysis.get("best_strategy_name", "").replace("_", " ")
            nw = analysis.get("projected_net_worth_best", 0)
            actions = analysis.get("next_actions", [])
            text = (
                f"{first}, your best strategy is **{name}** "
                f"(projected net worth ~{self._fmt(nw)} over 10 years).\n\n"
            )
            if actions:
                text += "Top actions:\n" + "\n".join(f"• {a.replace('**', '')}" for a in actions[:3])
            return text
        strategies = self.optimizer.evaluate(profile, horizon_years=10)
        if not strategies:
            return f"{first}, update your income and expenses so I can compute a plan."
        best = strategies[0]
        return (
            f"{first}, I'd lean toward **{best.name.replace('_', ' ')}** — "
            f"{best.description}\n\n"
            f"Projected net worth: ~{self._fmt(best.future_net_worth)}. "
            f"SIP ~{self._fmt(best.monthly_investment_suggested)}/mo, "
            f"extra loan paydown ~{self._fmt(best.loan_prepayment_monthly)}/mo.\n\n"
            "Hit **Compute my plan** on Strategy to save this to your dashboard."
        )

    def _goal_advice(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        if not profile.financial_goals:
            return f"{first}, add financial goals on the Strategy page — I'll track whether you're on pace."
        if analysis and analysis.get("goal_progress"):
            lines = [f"{first}, goal check-in:\n"]
            for g in analysis["goal_progress"]:
                status = "on track ✓" if g.get("on_track") else f"gap {self._fmt(g.get('gap', 0))}"
                lines.append(
                    f"• **{g['name']}**: {self._fmt(g.get('projected_amount', 0))} "
                    f"/ {self._fmt(g.get('target_amount', 0))} — {status}"
                )
            return "\n".join(lines)
        names = ", ".join(g.name for g in profile.financial_goals)
        return (
            f"{first}, you're tracking: {names}. "
            "Run **Compute my plan** to see projected progress against each target."
        )

    def _net_worth(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        assets = profile.savings + sum(a.value for a in profile.assets)
        debt = sum(l.amount for l in profile.loans)
        nw = assets - debt
        surplus = self._surplus(profile)
        months_ef = profile.savings / max(profile.expenses_monthly, 1)
        return (
            f"{first}, here's your snapshot:\n\n"
            f"• Net worth: **{self._fmt(nw)}** (assets {self._fmt(assets)} − debt {self._fmt(debt)})\n"
            f"• Monthly surplus: **{self._fmt(surplus)}**\n"
            f"• Emergency coverage: **{months_ef:.1f} months** of expenses\n"
            f"• Loans: {len(profile.loans)} · Assets: {len(profile.assets)} · Risk: {profile.risk_tolerance}"
        )

    def _general(self, profile: UserProfile, first: str, analysis: dict | None) -> str:
        return (
            f"{first}, I can help with:\n"
            "• **Debt payoff** — which loan to close first\n"
            "• **Invest vs prepay** — where surplus goes\n"
            "• **Emergency fund** — how much to keep liquid\n"
            "• **SIP amount** — monthly investment suggestion\n"
            "• **Strategy** — best plan for your profile\n"
            "• **Goals** — am I on track?\n\n"
            f"You have {self._fmt(self._surplus(profile))}/mo surplus and "
            f"{len(profile.loans)} loan(s). What would you like to explore?"
        )
