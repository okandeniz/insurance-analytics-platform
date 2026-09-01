from pathlib import Path

import joblib
import pandas as pd

from src.features.severity_features import (
    create_severity_features,
)
from src.modeling.severity_model import (
    MODEL_FEATURES,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "claim_severity_pipeline.joblib"
)


class ClaimSeverityService:
    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Severity model not found: {MODEL_PATH}"
            )

        self.model = joblib.load(MODEL_PATH)

    def predict(
        self,
        input_data: dict,
    ) -> float:

        raw_df = pd.DataFrame(
            [input_data]
        )

        feature_df = create_severity_features(
            raw_df
        )

        missing_features = [
            column
            for column in MODEL_FEATURES
            if column not in feature_df.columns
        ]

        if missing_features:
            raise ValueError(
                "Missing model features: "
                f"{missing_features}"
            )

        X = feature_df[
            MODEL_FEATURES
        ].copy()

        prediction = float(
            self.model.predict(X)[0]
        )

        # Damage amount cannot be negative.
        prediction = max(
            prediction,
            0.0,
        )

        return prediction