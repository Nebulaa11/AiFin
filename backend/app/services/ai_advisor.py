from __future__ import annotations

from app.config import get_settings
from app.models.schemas import StrategyResult, UserProfile
from app.services.local_agent import LocalFinanceAgent

_local_agent = LocalFinanceAgent()


class AIAdvisor:
    def explain(
        self,
        profile: UserProfile,
        best: StrategyResult,
        all_strategies: list[StrategyResult],
        loan_order: list[str],
        emergency_fund_target: float,
        emergency_fund_months: float,
        next_actions: list[str] | None = None,
    ) -> str:
        settings = get_settings()
        context = self._build_context(
            profile,
            best,
            all_strategies,
            loan_order,
            emergency_fund_target,
            emergency_fund_months,
            next_actions,
        )
        if settings.openai_api_key:
            return self._llm_explain(context)
        return self._fallback_explain(
            profile, best, loan_order, emergency_fund_target, emergency_fund_months, next_actions
        )

    def chat_with_history(
        self,
        profile: UserProfile | None,
        question: str,
        history: list[dict],
        user_name: str = "there",
        analysis: dict | None = None,
    ) -> str:
        settings = get_settings()
        if settings.openai_api_key:
            try:
                from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    temperature=0.4,
                )
                messages = [
                    SystemMessage(
                        content=(
                            "You are a calm, expert personal finance coach named AiFin. "
                            "Give practical, empathetic advice in 2-4 short paragraphs. "
                            "Reference the user's numbers when available. No legal/tax advice."
                        )
                    ),
                ]
                for m in history[-8:]:
                    if m["role"] == "user":
                        messages.append(HumanMessage(content=m["content"]))
                    else:
                        messages.append(AIMessage(content=m["content"]))
                messages.append(HumanMessage(content=question))
                resp = llm.invoke(messages)
                return getattr(resp, "content", str(resp))
            except Exception:
                pass

        return _local_agent.answer(profile, question, history, user_name, analysis)

    def chat(self, profile: UserProfile, question: str, analysis_context: dict | None = None) -> str:
        settings = get_settings()
        ctx_lines = [
            f"User age {profile.age}, risk {profile.risk_tolerance}, "
            f"income ₹{profile.income_monthly:,.0f}/mo, expenses ₹{profile.expenses_monthly:,.0f}/mo, "
            f"savings ₹{profile.savings:,.0f}.",
            f"Loans: {len(profile.loans)}. Goals: {len(profile.financial_goals)}.",
        ]
        if analysis_context:
            ctx_lines.append(f"Latest analysis: {analysis_context}")
        ctx_lines.append(f"Question: {question}")
        prompt = "\n".join(ctx_lines)

        if settings.openai_api_key:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    temperature=0.4,
                )
                messages = [
                    SystemMessage(
                        content=(
                            "You are a helpful personal finance coach. Answer briefly (2-4 paragraphs). "
                            "No legal or tax advice."
                        )
                    ),
                    HumanMessage(content=prompt),
                ]
                resp = llm.invoke(messages)
                return getattr(resp, "content", str(resp))
            except Exception as e:
                pass

        return _local_agent.answer(profile, question, None, "there", analysis_context)

    def _fallback_chat(self, profile: UserProfile, question: str, err: str = "") -> str:
        q = question.lower()
        parts = []
        if err:
            parts.append(f"[LLM unavailable: {err}]\n")
        if "loan" in q or "debt" in q:
            if profile.loans:
                top = max(profile.loans, key=lambda x: x.interest_rate)
                parts.append(
                    f"Focus extra payments on **{top.name}** ({top.interest_rate}% p.a.) — "
                    "highest-rate debt saves the most interest."
                )
            else:
                parts.append("You have no loans on file — surplus is best directed to investing and your emergency fund.")
        elif "invest" in q or "sip" in q:
            surplus = max(0, profile.income_monthly - profile.expenses_monthly)
            parts.append(
                f"With ~₹{surplus:,.0f}/month surplus, start a disciplined SIP aligned with your "
                f"{profile.risk_tolerance} risk tolerance after your emergency fund is covered."
            )
        elif "emergency" in q:
            target = profile.expenses_monthly * 6
            parts.append(
                f"Aim for ₹{target:,.0f} in liquid savings (roughly 6 months of expenses). "
                f"You currently have ₹{profile.savings:,.0f}."
            )
        else:
            parts.append(
                "Re-run the optimizer after updating your profile, or set OPENAI_API_KEY for richer follow-up answers."
            )
        parts.append(f"\n\n_Your question: {question}_")
        return "\n".join(parts)

    def _build_context(
        self,
        profile: UserProfile,
        best: StrategyResult,
        all_strategies: list[StrategyResult],
        loan_order: list[str],
        emergency_fund_target: float,
        emergency_fund_months: float,
        next_actions: list[str] | None,
    ) -> str:
        goals = ", ".join(g.name for g in profile.financial_goals) or "none"
        lines = [
            "You are a concise personal finance coach. Explain the recommendation in 3-5 short paragraphs.",
            "",
            f"User age: {profile.age}, risk: {profile.risk_tolerance}, dependents: {profile.dependents}.",
            f"Income monthly: {profile.income_monthly:.0f}, expenses: {profile.expenses_monthly:.0f}, savings: {profile.savings:.0f}.",
            f"Loans: {len(profile.loans)}. Assets: {len(profile.assets)}. Goals: {goals}.",
            f"Suggested payoff priority: {', '.join(loan_order) or 'none'}.",
            f"Emergency fund target ({emergency_fund_months:.1f} months expenses): {emergency_fund_target:.0f}.",
            "",
            f"Best strategy: {best.name}. {best.description}",
            f"Projected net worth (model horizon): {best.future_net_worth:.0f}. Goal fit: {best.goal_fit_score:.0f}/100.",
            f"Suggested monthly investment: {best.monthly_investment_suggested:.0f}; extra loan paydown: {best.loan_prepayment_monthly:.0f}.",
            "",
            "Alternatives:",
        ]
        for s in all_strategies[:4]:
            lines.append(
                f"- {s.name}: net worth ~{s.future_net_worth:.0f}, goal fit {s.goal_fit_score:.0f}"
            )
        if next_actions:
            lines.append("\nNext actions:")
            for a in next_actions:
                lines.append(f"- {a}")
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
        emergency_fund_months: float,
        next_actions: list[str] | None,
    ) -> str:
        parts = [
            f"Based on your profile (age {profile.age}, {profile.risk_tolerance} risk), "
            f"the optimizer favors **{best.name.replace('_', ' ')}**.",
            "",
            f"It projects ~{best.future_net_worth:,.0f} net worth in the model horizon "
            f"(goal fit {best.goal_fit_score:.0f}/100) with monthly investment "
            f"~{best.monthly_investment_suggested:,.0f} and extra loan paydown "
            f"~{best.loan_prepayment_monthly:,.0f}.",
            "",
        ]
        if loan_order:
            parts.append(f"For loans, **highest interest first**: {', '.join(loan_order)}.")
        else:
            parts.append("With no loans, the focus shifts to investing and liquidity.")
        parts.append(
            f"\n\nTarget an **emergency fund** of ~**{emergency_fund_target:,.0f}** "
            f"({emergency_fund_months:.1f} months of expenses)."
        )
        if profile.financial_goals:
            parts.append(f"\n\nTracking {len(profile.financial_goals)} goal(s): "
                         + ", ".join(g.name for g in profile.financial_goals) + ".")
        if next_actions:
            parts.append("\n\n**Next steps:**")
            for i, a in enumerate(next_actions, 1):
                parts.append(f"{i}. {a}")
        parts.append("\n\n_Powered by AiFin's free local finance model._")
        return "\n".join(parts)
