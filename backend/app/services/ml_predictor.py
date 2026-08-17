from __future__ import annotations

import json
from pathlib import Path

import joblib

from app.models.schemas import UserProfile

STRATEGY_LABEL_MAP = {
    "repay_loan_first": "repay_loans_aggressive",
    "invest_aggressive": "invest_aggressive",
    "balanced": "balanced",
    "emergency_first": "emergency_first",
    "repay_loans_aggressive": "repay_loans_aggressive",
}


class MLPredictor:
    def __init__(self, model_dir: Path | None = None):
        self.model_dir = model_dir or Path(__file__).resolve().parent.parent.parent / "models_saved"
        self._pipe = None
        self._loaded = False

    def _load(self) -> bool:
        if self._loaded:
            return self._pipe is not None
        self._loaded = True
        model_path = self.model_dir / "strategy_classifier.joblib"
        if not model_path.is_file():
            return False
        try:
            self._pipe = joblib.load(model_path)
            return True
        except Exception:
            self._pipe = None
            return False

    def _features(self, profile: UserProfile) -> dict:
        total_loan = sum(ln.amount for ln in profile.loans)
        weighted_rate = (
            sum(ln.amount * ln.interest_rate for ln in profile.loans) / total_loan if total_loan else 0.0
        )
        risk_map = {"low": 0, "medium": 1, "high": 2}
        ef_months = profile.savings / max(profile.expenses_monthly, 1.0)
        return {
            "age": profile.age,
            "income_monthly": profile.income_monthly,
            "expenses_monthly": profile.expenses_monthly,
            "savings": profile.savings,
            "total_loan_principal": total_loan,
            "weighted_loan_rate": weighted_rate,
            "months_to_emergency_fund": ef_months,
            "risk_tolerance_encoded": risk_map.get(profile.risk_tolerance, 1),
        }

    def predict_strategy(self, profile: UserProfile) -> str | None:
        if not self._load() or self._pipe is None:
            return None
        meta_path = self.model_dir / "strategy_classifier.meta.json"
        feature_columns: list[str] = []
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text())
            feature_columns = meta.get("feature_columns", [])
        row = self._features(profile)
        import pandas as pd

        if feature_columns:
            data = {c: row.get(c, 0) for c in feature_columns}
        else:
            data = row
        df = pd.DataFrame([data])
        try:
            label = str(self._pipe.predict(df)[0])
            return STRATEGY_LABEL_MAP.get(label, label)
        except Exception:
            return None
