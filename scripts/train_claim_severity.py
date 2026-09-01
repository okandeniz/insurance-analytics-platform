from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import pyodbc

from src.features.severity_features import (
    create_severity_features,
)
from src.modeling.severity_model import (
    MODEL_FEATURES,
    TARGET,
    build_severity_model,
)


# -------------------------------------------------
# Project paths
# -------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODELS_DIR = PROJECT_ROOT / "models"

MODEL_PATH = (
    MODELS_DIR
    / "claim_severity_pipeline.joblib"
)

METADATA_PATH = (
    MODELS_DIR
    / "claim_severity_metadata.json"
)


# -------------------------------------------------
# Data loading
# -------------------------------------------------

def load_severity_data() -> pd.DataFrame:
    """
    Load the claim severity modeling dataset
    from MySQL.
    """

    conn = pyodbc.connect(
        "DSN=InsuranceAnalytics;",
        autocommit=True,
    )

    query = """
    SELECT *
    FROM vw_auto_claim_severity_ml
    """

    try:
        df = pd.read_sql(
            query,
            conn,
        )
    finally:
        conn.close()

    return df


# -------------------------------------------------
# Training
# -------------------------------------------------

def train() -> None:

    print("Loading severity data...")

    df = load_severity_data()

    print(
        f"Loaded {len(df):,} severity records."
    )

    # Deterministic feature engineering
    feature_df = create_severity_features(
        df
    )

    # Model matrix
    X = feature_df[
        MODEL_FEATURES
    ].copy()

    y = feature_df[
        TARGET
    ].copy()

    # Basic validation
    if y.isna().any():
        raise ValueError(
            "Target contains missing values."
        )

    if (y <= 0).any():
        raise ValueError(
            "damage_amount must be positive."
        )

    missing_features = (
        set(MODEL_FEATURES)
        - set(feature_df.columns)
    )

    if missing_features:
        raise ValueError(
            "Missing model features: "
            f"{sorted(missing_features)}"
        )

    print(
        "Training shape:",
        X.shape,
    )

    # Build final model
    model = build_severity_model()

    print(
        "Training final severity model..."
    )

    model.fit(
        X,
        y,
    )

    # Smoke-test predictions
    predictions = model.predict(X)

    if (predictions < 0).any():
        raise ValueError(
            "Model produced negative predictions."
        )

    # Create output directory
    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save complete pipeline
    joblib.dump(
        model,
        MODEL_PATH,
    )

    # Save training metadata
    metadata = {
        "model_name": "RandomForestRegressor",
        "target": TARGET,
        "target_transformation": "log1p",
        "inverse_transformation": "expm1",
        "training_rows": int(len(X)),
        "feature_count": int(len(MODEL_FEATURES)),
        "features": MODEL_FEATURES,
        "target_mean": float(y.mean()),
        "target_median": float(y.median()),
        "training_prediction_mean": float(
            predictions.mean()
        ),
        "random_state": 42,
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )

    print("\nTraining completed.")

    print(
        "Model saved:",
        MODEL_PATH,
    )

    print(
        "Metadata saved:",
        METADATA_PATH,
    )


if __name__ == "__main__":
    train()