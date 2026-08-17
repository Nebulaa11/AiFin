import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import SavedProfile, TrainingJob
from app.models.schemas import (
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    SaveProfileRequest,
    SavedProfileResponse,
    TrainRequest,
    TrainResponse,
    UserProfile,
    WhatIfRequest,
    WhatIfResponse,
)
from app.ml.training import train_strategy_classifier
from app.ml.chat_training import train_chat_intent_classifier
from app.services.ai_advisor import AIAdvisor
from app.services.emergency_fund import emergency_fund_target
from app.services.finance_engine import FinanceEngine
from app.services.goal_planner import evaluate_goals
from app.services.insights import (
    build_assumptions,
    build_next_actions,
    debt_vs_invest_advice,
    sensitivity_analysis,
)
from app.services.optimizer import OptimizationEngine
from app.services.simulator import StrategySimulator
from app.services.timeline import build_timeline

router = APIRouter(prefix="/api/v1", tags=["finance"])

_engine = FinanceEngine()
_optimizer = OptimizationEngine()
_advisor = AIAdvisor()
_sim = StrategySimulator(_engine)

HORIZON_YEARS = 10


def _analyze_profile(profile: UserProfile, horizon_years: int = HORIZON_YEARS) -> AnalyzeResponse:
    ef_target, ef_months = emergency_fund_target(profile)
    metrics = _engine.profile_metrics(profile)
    strategies = _optimizer.evaluate(profile, horizon_years=horizon_years)
    if not strategies:
        raise HTTPException(status_code=400, detail="Could not evaluate strategies")
    best = strategies[0]
    loan_order = _optimizer.loan_repayment_order(profile)
    market_return = _sim.market_return_for_risk(profile.risk_tolerance)
    debt_advice = debt_vs_invest_advice(profile, market_return)
    next_actions = build_next_actions(profile, best, loan_order, ef_target, debt_advice)
    explanation = _advisor.explain(
        profile, best, strategies, loan_order, ef_target, ef_months, next_actions
    )
    timeline = build_timeline(
        profile,
        horizon_years * 12,
        best.monthly_investment_suggested,
        best.loan_prepayment_monthly,
        market_return,
    )
    goal_progress = evaluate_goals(
        profile, best.monthly_investment_suggested, best.loan_prepayment_monthly
    )
    assumptions = build_assumptions(profile, horizon_years, ef_months)
    sensitivity = sensitivity_analysis(
        profile,
        best.monthly_investment_suggested,
        best.loan_prepayment_monthly,
        horizon_years,
        market_return,
    )
    ml_hint = _optimizer.ml_strategy_hint(profile)

    return AnalyzeResponse(
        emergency_fund_target=ef_target,
        emergency_fund_months=ef_months,
        recommended_monthly_investment=best.monthly_investment_suggested,
        best_loan_repayment_order=loan_order,
        projected_net_worth_best=best.future_net_worth,
        strategies=strategies,
        best_strategy_name=best.name,
        explanation=explanation,
        engine_summary={
            "monthly_surplus": metrics["monthly_surplus"],
            "months_of_expenses_in_savings": metrics["months_of_expenses_in_savings"],
            "total_assets": metrics["total_assets"],
        },
        goal_progress=goal_progress,
        debt_vs_invest=debt_advice,
        next_actions=next_actions,
        assumptions=assumptions,
        timeline=timeline,
        sensitivity=sensitivity,
        ml_strategy_hint=ml_hint,
    )


@router.get("/health")
def health():
    return {"status": "ok", "service": "aifin-backend"}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(profile: UserProfile):
    return _analyze_profile(profile)


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(body: WhatIfRequest):
    profile = body.profile.model_copy(deep=True)
    if body.income_change_pct:
        factor = 1 + body.income_change_pct / 100.0
        profile.income_monthly *= factor

    base = _analyze_profile(profile, horizon_years=body.horizon_years)
    best = next((s for s in base.strategies if s.name == base.best_strategy_name), base.strategies[0])
    monthly_invest = body.monthly_investment if body.monthly_investment is not None else best.monthly_investment_suggested
    loan_prepay = (
        body.loan_prepayment_monthly
        if body.loan_prepayment_monthly is not None
        else best.loan_prepayment_monthly
    )
    market_return = _sim.market_return_for_risk(profile.risk_tolerance)
    months = body.horizon_years * 12
    nw = _engine.net_worth_projection(profile, months, monthly_invest, loan_prepay, market_return)
    if body.lump_sum_prepayment > 0:
        nw += body.lump_sum_prepayment * 0.5

    timeline = build_timeline(
        profile, months, monthly_invest, loan_prepay, market_return, body.lump_sum_prepayment
    )
    goal_progress = evaluate_goals(profile, monthly_invest, loan_prepay, body.horizon_years)

    return WhatIfResponse(
        projected_net_worth=nw,
        timeline=timeline,
        goal_progress=goal_progress,
        monthly_investment=monthly_invest,
        loan_prepayment_monthly=loan_prepay,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    answer = _advisor.chat(body.profile, body.question, body.analysis_context)
    return ChatResponse(answer=answer)


@router.post("/profiles", response_model=SavedProfileResponse)
def save_profile(body: SaveProfileRequest, db: Session = Depends(get_db)):
    row = SavedProfile(
        name=body.name,
        profile_json=body.profile.model_dump_json(),
        result_snapshot_json=json.dumps(body.result_snapshot) if body.result_snapshot else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SavedProfileResponse(
        id=row.id,
        name=row.name,
        profile=body.profile,
        result_snapshot=body.result_snapshot,
        created_at=row.created_at.isoformat(),
    )


@router.get("/profiles", response_model=list[SavedProfileResponse])
def list_profiles(db: Session = Depends(get_db)):
    rows = db.query(SavedProfile).order_by(SavedProfile.created_at.desc()).limit(20).all()
    out: list[SavedProfileResponse] = []
    for row in rows:
        out.append(
            SavedProfileResponse(
                id=row.id,
                name=row.name,
                profile=UserProfile.model_validate_json(row.profile_json),
                result_snapshot=json.loads(row.result_snapshot_json) if row.result_snapshot_json else None,
                created_at=row.created_at.isoformat(),
            )
        )
    return out


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    row = db.query(SavedProfile).filter(SavedProfile.id == profile_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(row)
    db.commit()
    return {"deleted": profile_id}


@router.post("/train", response_model=TrainResponse)
def train_model(body: TrainRequest, db: Session = Depends(get_db)):
    project_root = Path(__file__).resolve().parents[3]
    default_csv = project_root / "data" / "training_dataset_sample.csv"
    csv_path = Path(body.csv_path) if body.csv_path else default_csv
    if not csv_path.is_file():
        raise HTTPException(status_code=404, detail=f"CSV not found: {csv_path}")
    try:
        model_path, acc = train_strategy_classifier(csv_path, body.target_column)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    job = TrainingJob(
        dataset_path=str(csv_path),
        model_path=str(model_path),
        train_score=acc,
        notes="RandomForest strategy classifier",
    )
    db.add(job)
    db.commit()
    return TrainResponse(
        message="Model trained and saved",
        model_path=str(model_path),
        train_accuracy=acc,
    )


@router.post("/train/chat", response_model=TrainResponse)
def train_chat_model(body: TrainRequest, db: Session = Depends(get_db)):
    project_root = Path(__file__).resolve().parents[3]
    default_csv = project_root / "data" / "chat_intent_training.csv"
    csv_path = Path(body.csv_path) if body.csv_path else default_csv
    if not csv_path.is_file():
        raise HTTPException(status_code=404, detail=f"CSV not found: {csv_path}")
    try:
        model_path, acc = train_chat_intent_classifier(csv_path, target_column="intent")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    job = TrainingJob(
        dataset_path=str(csv_path),
        model_path=str(model_path),
        train_score=acc,
        notes="Chat intent classifier (TF-IDF + LogisticRegression)",
    )
    db.add(job)
    db.commit()
    return TrainResponse(
        message="Chat intent model trained and saved",
        model_path=str(model_path),
        train_accuracy=acc,
    )
