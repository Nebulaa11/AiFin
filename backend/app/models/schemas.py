from typing import Literal

from pydantic import BaseModel, Field


class LoanItem(BaseModel):
    name: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0, le=100)
    emi: float = Field(..., ge=0)


class AssetItem(BaseModel):
    type: str = Field(..., min_length=1)
    value: float = Field(..., ge=0)
    expected_return: float = Field(..., ge=0, le=100)


class FinancialGoal(BaseModel):
    name: str = Field(..., min_length=1)
    target_amount: float = Field(..., gt=0)
    target_years: float = Field(..., gt=0, le=50)
    goal_type: Literal["savings", "debt_free", "investment", "custom"] = "custom"


class UserProfile(BaseModel):
    age: int = Field(..., ge=18, le=100)
    income_monthly: float = Field(..., gt=0)
    expenses_monthly: float = Field(..., ge=0)
    savings: float = Field(..., ge=0)
    loans: list[LoanItem] = Field(default_factory=list)
    assets: list[AssetItem] = Field(default_factory=list)
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    financial_goals: list[FinancialGoal] = Field(default_factory=list)
    dependents: int = Field(default=0, ge=0, le=10)


class StrategyResult(BaseModel):
    name: str
    description: str
    future_net_worth: float
    risk_score: float
    cash_flow_stability: float
    composite_score: float
    monthly_investment_suggested: float
    loan_prepayment_monthly: float
    goal_fit_score: float = 0.0


class GoalProgress(BaseModel):
    name: str
    target_amount: float
    target_years: float
    projected_amount: float
    on_track: bool
    gap: float


class TimelinePoint(BaseModel):
    month: int
    net_worth: float
    investments: float
    total_debt: float
    liquid_savings: float


class DebtVsInvestAdvice(BaseModel):
    recommendation: Literal["prepay_debt", "invest", "balanced"]
    highest_loan_rate: float
    expected_return: float
    rationale: str


class SensitivityScenario(BaseModel):
    label: str
    return_pct: float
    projected_net_worth: float


class Assumptions(BaseModel):
    horizon_years: int
    market_return_pct: float
    emergency_fund_months: float
    inflation_pct: float
    tax_included: bool


class AnalyzeResponse(BaseModel):
    emergency_fund_target: float
    emergency_fund_months: float
    recommended_monthly_investment: float
    best_loan_repayment_order: list[str]
    projected_net_worth_best: float
    strategies: list[StrategyResult]
    best_strategy_name: str
    explanation: str
    engine_summary: dict
    goal_progress: list[GoalProgress]
    debt_vs_invest: DebtVsInvestAdvice
    next_actions: list[str]
    assumptions: Assumptions
    timeline: list[TimelinePoint]
    sensitivity: list[SensitivityScenario]
    ml_strategy_hint: str | None = None


class WhatIfRequest(BaseModel):
    profile: UserProfile
    monthly_investment: float | None = None
    loan_prepayment_monthly: float | None = None
    lump_sum_prepayment: float = Field(default=0, ge=0)
    income_change_pct: float = Field(default=0, ge=-50, le=100)
    horizon_years: int = Field(default=10, ge=1, le=40)


class WhatIfResponse(BaseModel):
    projected_net_worth: float
    timeline: list[TimelinePoint]
    goal_progress: list[GoalProgress]
    monthly_investment: float
    loan_prepayment_monthly: float


class ChatRequest(BaseModel):
    profile: UserProfile
    question: str = Field(..., min_length=1, max_length=1000)
    analysis_context: dict | None = None


class ChatResponse(BaseModel):
    answer: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class AuthUserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture_url: str | None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class UserProfileStore(BaseModel):
    profile: UserProfile
    last_analysis: dict | None = None


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ChatSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ChatSendResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    session_id: int


class SaveProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    profile: UserProfile
    result_snapshot: dict | None = None


class SavedProfileResponse(BaseModel):
    id: int
    name: str
    profile: UserProfile
    result_snapshot: dict | None
    created_at: str


class TrainRequest(BaseModel):
    csv_path: str | None = Field(default=None)
    target_column: str = "best_strategy_label"


class TrainResponse(BaseModel):
    message: str
    model_path: str
    train_accuracy: float | None = None
