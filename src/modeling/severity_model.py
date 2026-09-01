from __future__ import annotations

import numpy as np

from sklearn.compose import (
    ColumnTransformer,
    TransformedTargetRegressor,
)
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    RobustScaler,
    StandardScaler,
)


TARGET = "damage_amount"


STANDARD_COLUMNS = [
    "annual_premium",
    "client_age",
    "power_hp",
    "vehicle_age_at_claim",
]


ROBUST_COLUMNS = [
    "current_value",
    "premium_value_ratio",
    "log_declaration_lag",
]


CATEGORICAL_COLUMNS = [
    "claim_type",
    "risk_zone",
    "channel",
    "csp",
    "gender",
    "brand",
    "fuel_type",
    "vehicle_usage",
    "previous_claims_cat",
    "vehicle_age_group",
    "client_age_group",
    "occurrence_season",
]


MODEL_FEATURES = (
    STANDARD_COLUMNS
    + ROBUST_COLUMNS
    + CATEGORICAL_COLUMNS
)

def build_severity_preprocessor() -> ColumnTransformer:
    """
    Build the preprocessing pipeline for the
    final claim severity model.
    """

    standard_transformer = Pipeline(
        steps=[
            (
                "median_imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "standard_scaler",
                StandardScaler(),
            ),
        ]
    )

    robust_transformer = Pipeline(
        steps=[
            (
                "median_imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "robust_scaler",
                RobustScaler(),
            ),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "unknown_imputer",
                SimpleImputer(
                    strategy="constant",
                    fill_value="Unknown",
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "standard_num",
                standard_transformer,
                STANDARD_COLUMNS,
            ),
            (
                "robust_num",
                robust_transformer,
                ROBUST_COLUMNS,
            ),
            (
                "categorical",
                categorical_transformer,
                CATEGORICAL_COLUMNS,
            ),
        ],
        remainder="drop",
    )

def build_severity_model() -> TransformedTargetRegressor:
    """
    Build the final claim severity model.

    The target is trained on log1p(damage_amount).
    Predictions are automatically transformed back
    to the original damage scale.
    """

    preprocess = build_severity_preprocessor()

    regressor = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocess",
                preprocess,
            ),
            (
                "model",
                regressor,
            ),
        ]
    )

    return TransformedTargetRegressor(
        regressor=pipeline,
        func=np.log1p,
        inverse_func=np.expm1,
        check_inverse=False,
    )

