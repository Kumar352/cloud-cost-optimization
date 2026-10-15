"""Train an unsupervised anomaly detector on the currently loaded real CUR rows.

The model runs locally in memory; it does not upload billing data or persist a model
artifact. Scores are investigation hints, not validated predictions of waste.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler


NUMERIC_CANDIDATES = [
    "line_item_unblended_cost",
    "line_item_usage_amount",
    "line_item_unblended_rate",
    "line_item_blended_cost",
    "line_item_normalized_usage_amount",
]


def train_cur_anomaly_model(
    frame: pd.DataFrame,
    *,
    contamination: float = 0.03,
    random_state: int = 42,
    min_rows_per_currency: int = 30,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit one Isolation Forest per currency and return scored CUR rows plus metadata."""
    if not 0.005 <= contamination <= 0.20:
        raise ValueError("contamination must be between 0.005 and 0.20")
    if "Currency" not in frame.columns:
        raise ValueError("CUR data must include a Currency column")
    if frame.empty:
        raise ValueError("Cannot train the anomaly model on an empty CUR dataset")

    all_scores = []
    features_by_currency: dict[str, list[str]] = {}
    rows_trained = 0
    currencies_skipped: dict[str, str] = {}

    for currency, group in frame.groupby(frame["Currency"].astype(str), dropna=False):
        group = group.copy().reset_index(drop=True)
        candidate_columns = [col for col in NUMERIC_CANDIDATES if col in group.columns]
        numeric = pd.DataFrame(index=group.index)
        for col in candidate_columns:
            numeric[col] = pd.to_numeric(group[col], errors="coerce").replace(
                [np.inf, -np.inf], np.nan
            )

        feature_columns = [
            col for col in numeric.columns
            if numeric[col].notna().sum() >= min_rows_per_currency
            and numeric[col].nunique(dropna=True) > 1
        ]
        if len(group) < min_rows_per_currency:
            currencies_skipped[str(currency)] = (
                f"Only {len(group)} line items; requires at least {min_rows_per_currency}."
            )
            continue
        if not feature_columns:
            currencies_skipped[str(currency)] = "No variable numeric CUR features were available."
            continue

        x = numeric[feature_columns]
        model = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", RobustScaler()),
                (
                    "isolation_forest",
                    IsolationForest(
                        n_estimators=150,
                        contamination=contamination,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        predicted = model.fit_predict(x)
        estimator = model.named_steps["isolation_forest"]
        normality_score = model.decision_function(x)
        scored = group.copy()
        scored["ML_Anomaly_Flag"] = np.where(predicted == -1, "REVIEW", "TYPICAL")
        # Lower decision_function values are more anomalous; invert for an intuitive score.
        scored["ML_Anomaly_Score"] = -normality_score
        scored["ML_Model"] = "IsolationForest"
        scored["ML_Features"] = ", ".join(feature_columns)
        scored["ML_Currency"] = str(currency)
        all_scores.append(scored)
        features_by_currency[str(currency)] = feature_columns
        rows_trained += len(group)

    if not all_scores:
        details = " ".join(f"{c}: {reason}" for c, reason in currencies_skipped.items())
        raise ValueError(
            "Not enough usable numeric CUR line items to train a model. " + details
        )

    result = pd.concat(all_scores, ignore_index=True, sort=False)
    result = result.sort_values("ML_Anomaly_Score", ascending=False).reset_index(drop=True)
    flagged = int((result["ML_Anomaly_Flag"] == "REVIEW").sum())
    metadata = {
        "model_name": "IsolationForest",
        "rows_trained": int(rows_trained),
        "rows_scored": int(len(result)),
        "flagged_rows": flagged,
        "contamination": float(contamination),
        "features_by_currency": features_by_currency,
        "currencies_skipped": currencies_skipped,
        "persisted": False,
        "training_scope": "Current CUR rows in this Streamlit session; no labels required",
    }
    return result, metadata
