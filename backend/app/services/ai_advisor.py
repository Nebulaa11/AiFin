from __future__ import annotations

from app.config import get_settings
from app.models.schemas import StrategyResult, UserProfile


class AIAdvisor:
    def explain(
        self,
        profile: UserProfile,
        best: StrategyResult,
        all_strategies: list[StrategyResult],
        loan_order: list[str],
        emergency_fund_target: float,
    ) -> str:
        settings = get_settings()
        context = self._build_context(
            profile, best, all_strategies, loan_order, emergency_fund_target
        )
        if settings.openai_api_key:
            return self._llm_explain(context)
        return self._fallback_explain(profile, best, loan_order, emergency_fund_target)

    def _build_context(
        self,
        profile: UserProfile,
        best: StrategyResult,
        all_strategies: list[StrategyResult],
        loan_order: list[str],
        emergency_fund_target: float,
    ) -> str:
        lines = [
            "You are a concise personal finance coach. Explain the recommendation in 3-5 short paragraphs.",
            "",
            f"User age: {profile.age}, risk: {profile.risk_tolerance}.",
            f"Income monthly: {profile.income_monthly:.0f}, expenses: {profile.expenses_monthly:.0f}, savings: {profile.savings:.0f}.",
            f"Loans: {len(profile.loans)}. Suggested payoff priority: {', '.join(loan_order) or 'none'}.",
            f"Emergency fund target (6 months expenses): {emergency_fund_target:.0f}.",
            "",
            f"Best strategy: {best.name}. {best.description}",
            f"Projected net worth (model horizon): {best.future_net_worth:.0f}.",
            f"Suggested monthly investment: {best.monthly_investment_suggested:.0f}; extra loan paydown: {best.loan_prepayment_monthly:.0f}.",
            "",
            "Alternatives:",
        ]
        for s in all_strategies[:4]:
            lines.append(f"- {s.name}: net worth ~{s.future_net_worth:.0f}, score {s.composite_score:.0f}")
        return "\n".join(lines)

    def _llm_explain(self, context: str) -> str:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            settings = get_settings()
            llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=0.3,
            )
            messages = [
                SystemMessage(
                    content="You are a helpful financial advisor. No legal/tax advice; general principles only."
                ),
                HumanMessage(content=context),
            ]
            resp = llm.invoke(messages)
            return getattr(resp, "content", str(resp))
        except Exception as e:
            return (
                f"[LLM unavailable ({e!s}); using fallback summary.]\n\n"
                + self._fallback_from_context(context)
            )

    def _fallback_from_context(self, context: str) -> str:
        return context.split("Alternatives:")[0].strip()

    def _fallback_explain(
        self,
        profile: UserProfile,
        best: StrategyResult,
        loan_order: list[str],
        emergency_fund_target: float,
    ) -> str:
        parts = [
            f"Based on your profile (age {profile.age}, {profile.risk_tolerance} risk), "
            f"the optimizer favors **{best.name.replace('_', ' ')}**.",
            "",
            f"It projects a higher long-term net worth under this path (~{best.future_net_worth:,.0f} in the model horizon) "
            f"with suggested monthly investment (~{best.monthly_investment_suggested:,.0f}) "
            f"and extra loan principal (~{best.loan_prepayment_monthly:,.0f}).",
            "",
        ]
        if loan_order:
            parts.append(
                f"For loans, **highest interest first**: {', '.join(loan_order)}."
            )
        else:
            parts.append("With no loans, the focus shifts to investing and liquidity.")
        parts.append(
            f"\n\nTarget an **emergency fund** of about **{emergency_fund_target:,.0f}** (six months of expenses)."
        )
        parts.append(
            "\n\n_Set `OPENAI_API_KEY` in `backend/.env` for LLM explanations._"
        )
        return "\n".join(parts)
