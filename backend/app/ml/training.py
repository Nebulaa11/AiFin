from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def train_strategy_classifier(
    csv_path: Path,
    target_column: str = "best_strategy_label",
    model_dir: Path | None = None,
) -> tuple[Path, float | None]:
    df = pd.read_csv(csv_path)
    if target_column not in df.columns:
        raise ValueError(f"Missing target column {target_column}")

    y = df[target_column]
    X = df.drop(columns=[target_column])
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = [c for c in X.columns if c not in cat_cols]

    pre = ColumnTransformer(
        [
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ]
    )
    clf = RandomForestClassifier(n_estimators=80, random_state=42)
    pipe = Pipeline([("prep", pre), ("clf", clf)])

    if len(df) < 3:
        pipe.fit(X, y)
        acc = None
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        acc = float(accuracy_score(y_test, pred))

    model_dir = model_dir or Path(__file__).resolve().parent.parent.parent / "models_saved"
    model_dir.mkdir(parents=True, exist_ok=True)
    out = model_dir / "strategy_classifier.joblib"
    joblib.dump(pipe, out)

    meta = {
        "csv_path": str(csv_path),
        "target": target_column,
        "accuracy": acc,
        "feature_columns": list(X.columns),
    }
    (model_dir / "strategy_classifier.meta.json").write_text(json.dumps(meta, indent=2))
    return out, acc
