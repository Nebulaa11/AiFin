from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import TrainingJob
from app.models.schemas import AnalyzeResponse, TrainRequest, TrainResponse, UserProfile
from app.ml.training import train_strategy_classifier
from app.services.ai_advisor import AIAdvisor
from app.services.finance_engine import FinanceEngine
from app.services.optimizer import OptimizationEngine

router = APIRouter(prefix="/api/v1", tags=["finance"])

_engine = FinanceEngine()
_optimizer = OptimizationEngine()
_advisor = AIAdvisor()


@router.get("/health")
def health():
    return {"status": "ok", "service": "aifin-backend"}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(profile: UserProfile):
    emergency_fund_target = profile.expenses_monthly * 6.0
    metrics = _engine.profile_metrics(profile)
    strategies = _optimizer.evaluate(profile, horizon_years=10)
    if not strategies:
        raise HTTPException(status_code=400, detail="Could not evaluate strategies")
    best = strategies[0]
    loan_order = _optimizer.loan_repayment_order(profile)
    explanation = _advisor.explain(profile, best, strategies, loan_order, emergency_fund_target)
    return AnalyzeResponse(
        emergency_fund_target=emergency_fund_target,
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
    )


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
