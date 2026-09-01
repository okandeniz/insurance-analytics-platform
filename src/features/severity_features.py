from __future__ import annotations

import numpy as np
import pandas as pd


def create_severity_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create deterministic features for claim severity modeling.

    The function only uses information available in the input dataset.
    It does not fit any statistical transformer or use the target.

    Parameters
    ----------
    df : pd.DataFrame
        Raw severity modeling dataset.

    Returns
    -------
    pd.DataFrame
        Dataset with engineered severity features.
    """

    result = df.copy()

    # -------------------------------------------------
    # Date columns
    # -------------------------------------------------
    date_columns = [
        "occurrence_date",
        "declaration_date",
    ]

    for column in date_columns:
        if column in result.columns:
            result[column] = pd.to_datetime(
                result[column],
                errors="coerce",
            )

    # -------------------------------------------------
    # Previous claims as categorical
    # -------------------------------------------------
    if "previous_claims" in result.columns:
        result["previous_claims_cat"] = (
            result["previous_claims"]
            .astype("Int64")
            .astype("string")
            .fillna("Unknown")
        )

    # -------------------------------------------------
    # Premium relative to vehicle value
    # -------------------------------------------------
    if {
        "annual_premium",
        "current_value",
    }.issubset(result.columns):

        result["premium_value_ratio"] = (
            result["annual_premium"]
            / result["current_value"]
        )

    # -------------------------------------------------
    # Vehicle value per horsepower
    # -------------------------------------------------
    if {
        "current_value",
        "power_hp",
    }.issubset(result.columns):

        result["value_per_hp"] = (
            result["current_value"]
            / result["power_hp"]
        )

    # -------------------------------------------------
    # Declaration lag transformation
    # -------------------------------------------------
    if "declaration_lag_days" in result.columns:

        result["log_declaration_lag"] = np.log1p(
            result["declaration_lag_days"]
        )

    # -------------------------------------------------
    # Vehicle age group
    # -------------------------------------------------
    if "vehicle_age_at_claim" in result.columns:

        result["vehicle_age_group"] = pd.cut(
            result["vehicle_age_at_claim"],
            bins=[
                -1,
                3,
                7,
                np.inf,
            ],
            labels=[
                "0-3",
                "4-7",
                "8+",
            ],
        ).astype("object")

    # -------------------------------------------------
    # Client age group
    # -------------------------------------------------
    if "client_age" in result.columns:

        result["client_age_group"] = pd.cut(
            result["client_age"],
            bins=[
                17,
                29,
                39,
                49,
                59,
                np.inf,
            ],
            labels=[
                "18-29",
                "30-39",
                "40-49",
                "50-59",
                "60+",
            ],
        ).astype("object")

    # -------------------------------------------------
    # Claim occurrence season
    # -------------------------------------------------
    if "occurrence_date" in result.columns:

        month = result[
            "occurrence_date"
        ].dt.month

        season_map = {
            12: "Winter",
            1: "Winter",
            2: "Winter",

            3: "Spring",
            4: "Spring",
            5: "Spring",

            6: "Summer",
            7: "Summer",
            8: "Summer",

            9: "Autumn",
            10: "Autumn",
            11: "Autumn",
        }

        result["occurrence_season"] = (
            month.map(season_map)
        )

    return result