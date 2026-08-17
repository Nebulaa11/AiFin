from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def train_chat_intent_classifier(
    csv_path: Path,
    target_column: str = "intent",
    text_column: str = "question",
    model_dir: Path | None = None,
) -> tuple[Path, float | None]:
    df = pd.read_csv(csv_path)
    if target_column not in df.columns or text_column not in df.columns:
        raise ValueError(f"CSV must include '{text_column}' and '{target_column}' columns")

    X = df[text_column].astype(str)
    y = df[target_column].astype(str)

    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, lowercase=True)),
            ("clf", LogisticRegression(max_iter=500, random_state=42)),
        ]
    )

    if len(df) < 4:
        pipe.fit(X, y)
        acc = None
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        acc = float(accuracy_score(y_test, pred))

    model_dir = model_dir or Path(__file__).resolve().parent.parent.parent / "models_saved"
    model_dir.mkdir(parents=True, exist_ok=True)
    out = model_dir / "chat_intent_classifier.joblib"
    joblib.dump(pipe, out)

    meta = {
        "csv_path": str(csv_path),
        "target": target_column,
        "text_column": text_column,
        "accuracy": acc,
        "intents": sorted(y.unique().tolist()),
    }
    (model_dir / "chat_intent_classifier.meta.json").write_text(json.dumps(meta, indent=2))
    return out, acc
