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


class UserProfile(BaseModel):
    age: int = Field(..., ge=18, le=100)
    income_monthly: float = Field(..., gt=0)
    expenses_monthly: float = Field(..., ge=0)
    savings: float = Field(..., ge=0)
    loans: list[LoanItem] = Field(default_factory=list)
    assets: list[AssetItem] = Field(default_factory=list)
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    financial_goals: list[str] = Field(default_factory=list)


class StrategyResult(BaseModel):
    name: str
    description: str
    future_net_worth: float
    risk_score: float
    cash_flow_stability: float
    composite_score: float
    monthly_investment_suggested: float
    loan_prepayment_monthly: float


class AnalyzeResponse(BaseModel):
    emergency_fund_target: float
    recommended_monthly_investment: float
    best_loan_repayment_order: list[str]
    projected_net_worth_best: float
    strategies: list[StrategyResult]
    best_strategy_name: str
    explanation: str
    engine_summary: dict


class TrainRequest(BaseModel):
    csv_path: str | None = Field(default=None)
    target_column: str = "best_strategy_label"


class TrainResponse(BaseModel):
    message: str
    model_path: str
    train_accuracy: float | None = None
