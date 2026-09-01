"""
Reusable data-cleaning utilities for the Insurance Analytics Platform.

The transformations implemented in this module are based on the cleaning
rules validated in notebooks/02_data_cleaning.ipynb.

The module is responsible for:
- Monetary value standardization
- Mixed-format date parsing
- Ambiguous date resolution
- Categorical standardization
- Vehicle power standardization
- Final schema preparation
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# Cleaning constants
# ---------------------------------------------------------------------

MIN_CONTRACT_DAYS = 305
MAX_CONTRACT_DAYS = 425
TYPICAL_CONTRACT_DAYS = 365

MIN_CLAIM_LAG_DAYS = 0
MAX_CLAIM_LAG_DAYS = 62

CV_TO_HP = 0.98632
KW_TO_HP = 1.34102

__all__ = [
    "clean_all_datasets",
    "clean_contracts",
    "clean_claims",
    "clean_vehicles",
    "parse_monetary_series",
    "parse_unambiguous_date",
    "get_ambiguous_date_candidates",
    "standardize_gender",
    "split_city_postal",
]

def parse_monetary_series(series: pd.Series) -> pd.Series:
    """
    Convert formatted monetary strings into nullable numeric values.
    """

    cleaned = (
        series
        .astype("string")
        .str.strip()
        .str.replace(r"[^\d.\-]", "", regex=True)
        .replace("", pd.NA)
    )

    return pd.to_numeric(
        cleaned,
        errors="coerce",
    ).astype("Float64")

def parse_unambiguous_date(value: object) -> pd.Timestamp:
    """
    Parse a date only when its representation can be interpreted
    unambiguously.
    """
    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    # ISO format: YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return pd.to_datetime(
            value,
            format="%Y-%m-%d",
            errors="coerce",
        )

    # Explicit day-first format: DD-MM-YYYY
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", value):
        return pd.to_datetime(
            value,
            format="%d-%m-%Y",
            errors="coerce",
        )

    # Slash-separated format
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        first, second, _ = map(
            int,
            value.split("/"),
        )

        # DD/MM/YYYY
        if first > 12:
            return pd.to_datetime(
                value,
                format="%d/%m/%Y",
                errors="coerce",
            )

        # MM/DD/YYYY
        if second > 12:
            return pd.to_datetime(
                value,
                format="%m/%d/%Y",
                errors="coerce",
            )

        # Ambiguous
        return pd.NaT

    return pd.NaT

def get_ambiguous_date_candidates(
    value: object,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Return the two possible interpretations of an ambiguous
    slash-separated date.

    Example
    -------
    '08/03/2025'

    candidate 1 -> 2025-03-08
    candidate 2 -> 2025-08-03
    """
    if pd.isna(value):
        return pd.NaT, pd.NaT

    value = str(value).strip()

    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return pd.NaT, pd.NaT

    first, second, year = map(
        int,
        value.split("/"),
    )

    if first > 12 or second > 12:
        return pd.NaT, pd.NaT

    day_first = pd.Timestamp(
        year=year,
        month=second,
        day=first,
    )

    month_first = pd.Timestamp(
        year=year,
        month=first,
        day=second,
    )

    return day_first, month_first

def standardize_gender(series: pd.Series) -> pd.Series:
    """
    Standardize gender category labels while preserving missing values.

    F -> Female
    M -> Male
    """
    mapping = {
        "F": "Female",
        "M": "Male",
    }

    return series.replace(mapping)

def split_city_postal(
    series: pd.Series,
) -> pd.DataFrame:
    """
    Split values such as 'Paris_75001' into city and postal code.

    Returns
    -------
    DataFrame with:
        city
        postal_code
    """
    split_values = (
        series
        .astype("string")
        .str.rsplit("_", n=1, expand=True)
    )

    split_values.columns = [
        "city",
        "postal_code",
    ]

    return split_values

def _resolve_single_ambiguous_contract_date(
    raw_value: object,
    fixed_date: pd.Timestamp,
    *,
    ambiguous_is_start: bool,
) -> pd.Timestamp:
    """
    Resolve one ambiguous contract date using the known paired date.

    Candidate dates are evaluated using:
    1. Valid contract duration range.
    2. Distance from the typical 365-day contract duration.

    If multiple distinct candidates remain equally plausible,
    the date is intentionally left unresolved.
    """
    candidate_1, candidate_2 = get_ambiguous_date_candidates(
        raw_value
    )

    candidates = [
        candidate
        for candidate in {candidate_1, candidate_2}
        if pd.notna(candidate)
    ]

    valid_candidates = []

    for candidate in candidates:

        if ambiguous_is_start:
            duration = (fixed_date - candidate).days
        else:
            duration = (candidate - fixed_date).days

        if MIN_CONTRACT_DAYS <= duration <= MAX_CONTRACT_DAYS:
            valid_candidates.append(
                (candidate, duration)
            )

    if not valid_candidates:
        return pd.NaT

    if len(valid_candidates) == 1:
        return valid_candidates[0][0]

    distances = [
        abs(duration - TYPICAL_CONTRACT_DAYS)
        for _, duration in valid_candidates
    ]

    min_distance = min(distances)

    best_candidates = [
        candidate
        for candidate, duration in valid_candidates
        if abs(duration - TYPICAL_CONTRACT_DAYS)
        == min_distance
    ]

    if len(best_candidates) == 1:
        return best_candidates[0]

    return pd.NaT

def _resolve_both_ambiguous_contract_dates(
    raw_start_date: object,
    raw_end_date: object,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """
    Resolve a contract where both start and end dates are ambiguous.

    All unique start-end candidate combinations are evaluated.

    The pair whose duration is valid and closest to the typical
    365-day contract duration is selected.

    If multiple distinct date pairs remain equally plausible,
    both values remain unresolved.
    """
    start_candidates = {
        candidate
        for candidate in get_ambiguous_date_candidates(
            raw_start_date
        )
        if pd.notna(candidate)
    }

    end_candidates = {
        candidate
        for candidate in get_ambiguous_date_candidates(
            raw_end_date
        )
        if pd.notna(candidate)
    }

    valid_pairs = []

    for start_candidate in start_candidates:
        for end_candidate in end_candidates:

            duration = (
                end_candidate - start_candidate
            ).days

            if (
                MIN_CONTRACT_DAYS
                <= duration
                <= MAX_CONTRACT_DAYS
            ):
                valid_pairs.append(
                    (
                        start_candidate,
                        end_candidate,
                        duration,
                    )
                )

    if not valid_pairs:
        return pd.NaT, pd.NaT

    distances = [
        abs(duration - TYPICAL_CONTRACT_DAYS)
        for _, _, duration in valid_pairs
    ]

    min_distance = min(distances)

    best_pairs = [
        (start_date, end_date)
        for start_date, end_date, duration
        in valid_pairs
        if abs(duration - TYPICAL_CONTRACT_DAYS)
        == min_distance
    ]

    # Remove duplicated calendar-date pairs.
    best_pairs = list(dict.fromkeys(best_pairs))

    if len(best_pairs) == 1:
        return best_pairs[0]

    return pd.NaT, pd.NaT

def clean_contracts(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and standardize the contracts dataset.

    Transformations
    ---------------
    - Standardize annual premium as numeric.
    - Standardize gender categories.
    - Split city and postal code.
    - Parse mixed-format contract dates.
    - Resolve ambiguous dates using contract-duration rules.
    - Preserve genuinely unresolved dates as NaT.
    - Standardize final data types.
    - Return the final analytical schema.

    The input DataFrame is not modified.
    """
    result = df.copy()

    # ---------------------------------------------------------
    # Monetary cleaning
    # ---------------------------------------------------------

    result["annual_premium"] = parse_monetary_series(
        result["annual_premium"]
    )

    # ---------------------------------------------------------
    # Categorical cleaning
    # ---------------------------------------------------------

    result["gender"] = standardize_gender(
        result["gender"]
    )

    # ---------------------------------------------------------
    # City / postal code separation
    # ---------------------------------------------------------

    city_postal = split_city_postal(
        result["city_postal"]
    )

    result["city"] = city_postal["city"]
    result["postal_code"] = city_postal["postal_code"]

    # ---------------------------------------------------------
    # Initial date parsing
    # ---------------------------------------------------------

    result["start_date_parsed"] = (
        result["start_date"]
        .apply(parse_unambiguous_date)
    )

    result["end_date_parsed"] = (
        result["end_date"]
        .apply(parse_unambiguous_date)
    )

    # ---------------------------------------------------------
    # Resolve ambiguous start dates when end date is known
    # ---------------------------------------------------------

    start_mask = (
        result["start_date_parsed"].isna()
        & result["end_date_parsed"].notna()
    )

    for idx in result.index[start_mask]:

        result.at[
            idx,
            "start_date_parsed",
        ] = _resolve_single_ambiguous_contract_date(
            result.at[idx, "start_date"],
            result.at[idx, "end_date_parsed"],
            ambiguous_is_start=True,
        )

    # ---------------------------------------------------------
    # Resolve ambiguous end dates when start date is known
    # ---------------------------------------------------------

    end_mask = (
        result["end_date_parsed"].isna()
        & result["start_date_parsed"].notna()
    )

    for idx in result.index[end_mask]:

        result.at[
            idx,
            "end_date_parsed",
        ] = _resolve_single_ambiguous_contract_date(
            result.at[idx, "end_date"],
            result.at[idx, "start_date_parsed"],
            ambiguous_is_start=False,
        )

    # ---------------------------------------------------------
    # Resolve contracts where both dates remain ambiguous
    # ---------------------------------------------------------

    both_mask = (
        result["start_date_parsed"].isna()
        & result["end_date_parsed"].isna()
    )

    for idx in result.index[both_mask]:

        resolved_start, resolved_end = (
            _resolve_both_ambiguous_contract_dates(
                result.at[idx, "start_date"],
                result.at[idx, "end_date"],
            )
        )

        result.at[
            idx,
            "start_date_parsed",
        ] = resolved_start

        result.at[
            idx,
            "end_date_parsed",
        ] = resolved_end

    # ---------------------------------------------------------
    # Final clean schema
    # ---------------------------------------------------------

    result = result[
        [
            "contract_id",
            "client_id",
            "client_name",
            "product",
            "start_date_parsed",
            "end_date_parsed",
            "annual_premium",
            "status",
            "city",
            "postal_code",
            "risk_zone",
            "client_age",
            "channel",
            "csp",
            "gender",
        ]
    ].copy()

    result = result.rename(
        columns={
            "start_date_parsed": "start_date",
            "end_date_parsed": "end_date",
            "status": "contract_status",
        }
    )

    # ---------------------------------------------------------
    # Final dtypes
    # ---------------------------------------------------------

    result["client_age"] = (
        result["client_age"]
        .astype("Int64")
    )

    result["postal_code"] = (
        result["postal_code"]
        .astype("string")
    )

    return result

def _is_valid_claim_lag(
    occurrence_date: pd.Timestamp,
    declaration_date: pd.Timestamp,
) -> bool:
    """Check whether a claim declaration lag is within the valid range."""
    if pd.isna(occurrence_date) or pd.isna(declaration_date):
        return False

    lag_days = (
        declaration_date - occurrence_date
    ).days

    return (
        MIN_CLAIM_LAG_DAYS
        <= lag_days
        <= MAX_CLAIM_LAG_DAYS
    )


def _unique_date_candidates(
    value: object,
) -> list[pd.Timestamp]:
    """
    Return unique valid interpretations of an ambiguous date.

    Duplicate calendar dates are removed. This is useful for values
    such as 03/03/2025, where both day-first and month-first
    interpretations represent the same date.
    """
    candidates = get_ambiguous_date_candidates(value)

    return list(
        dict.fromkeys(
            candidate
            for candidate in candidates
            if pd.notna(candidate)
        )
    )


def _resolve_ambiguous_claim_occurrence(
    raw_occurrence_date: object,
    declaration_date: pd.Timestamp,
) -> tuple[pd.Timestamp, pd.Timestamp, bool]:
    """
    Resolve an ambiguous claim occurrence date.

    Direct interpretations are evaluated first. If no direct
    interpretation produces a valid declaration lag, the previously
    validated occurrence/declaration reversal rule is evaluated.
    """
    candidates = _unique_date_candidates(
        raw_occurrence_date
    )

    direct_valid = [
        candidate
        for candidate in candidates
        if _is_valid_claim_lag(
            candidate,
            declaration_date,
        )
    ]

    # Exactly one direct interpretation is valid.
    if len(direct_valid) == 1:
        return (
            direct_valid[0],
            declaration_date,
            False,
        )

    # Multiple direct interpretations remain plausible.
    if len(direct_valid) > 1:
        return (
            pd.NaT,
            declaration_date,
            False,
        )

    # Test the reversal hypothesis.
    swapped_valid = [
        candidate
        for candidate in candidates
        if _is_valid_claim_lag(
            declaration_date,
            candidate,
        )
    ]

    if len(swapped_valid) == 1:
        return (
            declaration_date,
            swapped_valid[0],
            True,
        )

    return (
        pd.NaT,
        declaration_date,
        False,
    )

def _resolve_ambiguous_claim_declaration(
    occurrence_date: pd.Timestamp,
    raw_declaration_date: object,
) -> tuple[pd.Timestamp, pd.Timestamp, bool]:
    """
    Resolve an ambiguous claim declaration date.

    Direct interpretations are evaluated first. If none are valid,
    the occurrence/declaration reversal hypothesis is evaluated.
    """
    candidates = _unique_date_candidates(
        raw_declaration_date
    )

    direct_valid = [
        candidate
        for candidate in candidates
        if _is_valid_claim_lag(
            occurrence_date,
            candidate,
        )
    ]

    if len(direct_valid) == 1:
        return (
            occurrence_date,
            direct_valid[0],
            False,
        )

    # Example: CLM_0000014.
    # Two plausible declaration dates -> preserve ambiguity.
    if len(direct_valid) > 1:
        return (
            occurrence_date,
            pd.NaT,
            False,
        )

    swapped_valid = [
        candidate
        for candidate in candidates
        if _is_valid_claim_lag(
            candidate,
            occurrence_date,
        )
    ]

    if len(swapped_valid) == 1:
        return (
            swapped_valid[0],
            occurrence_date,
            True,
        )

    return (
        occurrence_date,
        pd.NaT,
        False,
    )

def _resolve_both_ambiguous_claim_dates(
    raw_occurrence_date: object,
    raw_declaration_date: object,
) -> tuple[pd.Timestamp, pd.Timestamp, bool]:
    """
    Resolve a claim where both occurrence and declaration dates
    are ambiguous.

    Direct date combinations are evaluated first. If no direct
    combination is valid, the validated date-reversal hypothesis
    is evaluated.

    Multiple equally plausible combinations remain unresolved.
    """
    occurrence_candidates = _unique_date_candidates(
        raw_occurrence_date
    )

    declaration_candidates = _unique_date_candidates(
        raw_declaration_date
    )

    direct_pairs = []

    for occurrence_candidate in occurrence_candidates:
        for declaration_candidate in declaration_candidates:

            if _is_valid_claim_lag(
                occurrence_candidate,
                declaration_candidate,
            ):
                direct_pairs.append(
                    (
                        occurrence_candidate,
                        declaration_candidate,
                    )
                )

    direct_pairs = list(
        dict.fromkeys(direct_pairs)
    )

    if len(direct_pairs) == 1:
        occurrence, declaration = direct_pairs[0]

        return occurrence, declaration, False

    if len(direct_pairs) > 1:
        return pd.NaT, pd.NaT, False

    # No valid direct interpretation.
    # Test reversed roles.
    swapped_pairs = []

    for occurrence_candidate in occurrence_candidates:
        for declaration_candidate in declaration_candidates:

            corrected_occurrence = declaration_candidate
            corrected_declaration = occurrence_candidate

            if _is_valid_claim_lag(
                corrected_occurrence,
                corrected_declaration,
            ):
                swapped_pairs.append(
                    (
                        corrected_occurrence,
                        corrected_declaration,
                    )
                )

    swapped_pairs = list(
        dict.fromkeys(swapped_pairs)
    )

    if len(swapped_pairs) == 1:
        occurrence, declaration = swapped_pairs[0]

        return occurrence, declaration, True

    return pd.NaT, pd.NaT, False

def clean_claims(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and standardize the claims dataset.

    Transformations
    ---------------
    - Standardize monetary fields.
    - Parse mixed-format occurrence and declaration dates.
    - Correct chronologically reversed claim dates.
    - Resolve ambiguous dates using the validated 0-62 day
      declaration-lag rule.
    - Preserve genuinely ambiguous dates as NaT.
    - Create declaration lag and date-correction audit fields.
    - Return the final analytical schema.

    The input DataFrame is not modified.
    """
    result = df.copy()

    # ---------------------------------------------------------
    # Monetary cleaning
    # ---------------------------------------------------------

    result["damage_amount"] = parse_monetary_series(
        result["damage_amount"]
    )

    result["indemnified_amount"] = parse_monetary_series(
        result["indemnified_amount"]
    )

    # ---------------------------------------------------------
    # Initial date parsing
    # ---------------------------------------------------------

    result["occurrence_date_parsed"] = (
        result["occurrence_date"]
        .apply(parse_unambiguous_date)
    )

    result["declaration_date_parsed"] = (
        result["declaration_date"]
        .apply(parse_unambiguous_date)
    )

    result["claim_dates_swapped"] = False

    # ---------------------------------------------------------
    # Resolve claim dates
    # ---------------------------------------------------------

    for idx in result.index:

        occurrence = result.at[
            idx,
            "occurrence_date_parsed",
        ]

        declaration = result.at[
            idx,
            "declaration_date_parsed",
        ]

        raw_occurrence = result.at[
            idx,
            "occurrence_date",
        ]

        raw_declaration = result.at[
            idx,
            "declaration_date",
        ]

        swapped = False

        # -----------------------------------------------------
        # Both dates already parsed
        # -----------------------------------------------------

        if (
            pd.notna(occurrence)
            and pd.notna(declaration)
        ):
            if _is_valid_claim_lag(
                occurrence,
                declaration,
            ):
                resolved_occurrence = occurrence
                resolved_declaration = declaration

            elif _is_valid_claim_lag(
                declaration,
                occurrence,
            ):
                resolved_occurrence = declaration
                resolved_declaration = occurrence
                swapped = True

            else:
                # Preserve the parsed values and allow final
                # validation to surface an unsupported case.
                resolved_occurrence = occurrence
                resolved_declaration = declaration

        # -----------------------------------------------------
        # Occurrence ambiguous, declaration known
        # -----------------------------------------------------

        elif (
            pd.isna(occurrence)
            and pd.notna(declaration)
        ):
            (
                resolved_occurrence,
                resolved_declaration,
                swapped,
            ) = _resolve_ambiguous_claim_occurrence(
                raw_occurrence,
                declaration,
            )

        # -----------------------------------------------------
        # Declaration ambiguous, occurrence known
        # -----------------------------------------------------

        elif (
            pd.notna(occurrence)
            and pd.isna(declaration)
        ):
            (
                resolved_occurrence,
                resolved_declaration,
                swapped,
            ) = _resolve_ambiguous_claim_declaration(
                occurrence,
                raw_declaration,
            )

        # -----------------------------------------------------
        # Both dates ambiguous
        # -----------------------------------------------------

        else:
            (
                resolved_occurrence,
                resolved_declaration,
                swapped,
            ) = _resolve_both_ambiguous_claim_dates(
                raw_occurrence,
                raw_declaration,
            )

        result.at[
            idx,
            "occurrence_date_parsed",
        ] = resolved_occurrence

        result.at[
            idx,
            "declaration_date_parsed",
        ] = resolved_declaration

        result.at[
            idx,
            "claim_dates_swapped",
        ] = swapped

    # ---------------------------------------------------------
    # Declaration lag
    # ---------------------------------------------------------

    result["declaration_lag_days"] = (
        result["declaration_date_parsed"]
        - result["occurrence_date_parsed"]
    ).dt.days

    # ---------------------------------------------------------
    # Final clean schema
    # ---------------------------------------------------------

    result = result[
        [
            "claim_id",
            "contract_id",
            "occurrence_date_parsed",
            "declaration_date_parsed",
            "claim_type",
            "damage_amount",
            "indemnified_amount",
            "status",
            "expert_id",
            "liability",
            "declaration_lag_days",
            "claim_dates_swapped",
        ]
    ].copy()

    result = result.rename(
        columns={
            "occurrence_date_parsed": "occurrence_date",
            "declaration_date_parsed": "declaration_date",
            "status": "claim_status",
        }
    )

    # ---------------------------------------------------------
    # Final dtypes
    # ---------------------------------------------------------

    result["declaration_lag_days"] = (
        result["declaration_lag_days"]
        .astype("Int64")
    )

    result["claim_dates_swapped"] = (
        result["claim_dates_swapped"]
        .astype(bool)
    )

    return result

def clean_vehicles(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and standardize the vehicles dataset.

    Transformations
    ---------------
    - Standardize current vehicle value as numeric.
    - Extract numeric vehicle power values.
    - Identify original power units.
    - Convert HP, CV, and kW values to standardized horsepower.
    - Treat unitless numeric power values as HP-equivalent.
    - Preserve missing vehicle attributes.
    - Standardize final data types.
    - Return the final analytical schema.

    The input DataFrame is not modified.
    """
    result = df.copy()

    # ---------------------------------------------------------
    # Monetary cleaning
    # ---------------------------------------------------------

    result["current_value"] = parse_monetary_series(
        result["current_value"]
    )

    # ---------------------------------------------------------
    # Power parsing
    # ---------------------------------------------------------

    power_str = (
        result["power"]
        .astype("string")
        .str.strip()
    )

    result["power_value_raw"] = (
        power_str
        .str.extract(
            r"(\d+(?:\.\d+)?)",
            expand=False,
        )
        .astype("Float64")
    )

    # ---------------------------------------------------------
    # Power unit classification
    # ---------------------------------------------------------

    result["power_unit"] = pd.Series(
        pd.NA,
        index=result.index,
        dtype="string",
    )

    hp_mask = (
        power_str
        .str.contains(
            "hp",
            case=False,
            regex=False,
            na=False,
        )
    )

    cv_mask = (
        power_str
        .str.contains(
            "cv",
            case=False,
            regex=False,
            na=False,
        )
    )

    kw_mask = (
        power_str
        .str.contains(
            "kw",
            case=False,
            regex=False,
            na=False,
        )
    )

    unitless_mask = (
        power_str
        .str.fullmatch(
            r"\d+(?:\.\d+)?",
            na=False,
        )
    )

    result.loc[
        hp_mask,
        "power_unit",
    ] = "HP"

    result.loc[
        cv_mask,
        "power_unit",
    ] = "CV"

    result.loc[
        kw_mask,
        "power_unit",
    ] = "kW"

    result.loc[
        unitless_mask,
        "power_unit",
    ] = "Unitless"

    # ---------------------------------------------------------
    # Standardize power to HP
    # ---------------------------------------------------------

    result["power_hp"] = pd.Series(
        pd.NA,
        index=result.index,
        dtype="Float64",
    )

    result.loc[
        result["power_unit"].eq("HP").fillna(False),
        "power_hp",
    ] = result["power_value_raw"]

    result.loc[
        result["power_unit"].eq("CV").fillna(False),
        "power_hp",
    ] = (
        result["power_value_raw"] * CV_TO_HP
    )

    result.loc[
        result["power_unit"].eq("kW").fillna(False),
        "power_hp",
    ] = (
        result["power_value_raw"] * KW_TO_HP
    )

    result.loc[
        result["power_unit"].eq("Unitless").fillna(False),
        "power_hp",
    ] = result["power_value_raw"]

    result["power_hp"] = (
        result["power_hp"]
        .round(2)
    )

    # ---------------------------------------------------------
    # Rename SQL-sensitive columns
    # ---------------------------------------------------------

    result = result.rename(
        columns={
            "usage": "vehicle_usage",
            }
    )

    # ---------------------------------------------------------
    # Final schema
    # ---------------------------------------------------------

    result = result[
        [
            "contract_id",
            "brand",
            "model",
            "year",
            "power_hp",
            "power_unit",
            "fuel_type",
            "current_value",
            "color",
            "vehicle_usage",
            "previous_claims",
        ]
    ].copy()

    # ---------------------------------------------------------
    # Final dtypes
    # ---------------------------------------------------------

    result["year"] = (
        result["year"]
        .astype("Int64")
    )

    result["previous_claims"] = (
        result["previous_claims"]
        .astype("Int64")
    )

    return result

def clean_all_datasets(
    contracts: pd.DataFrame,
    claims: pd.DataFrame,
    vehicles: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Clean all raw insurance datasets using the validated
    project cleaning rules.

    Parameters
    ----------
    contracts
        Raw contracts dataset.

    claims
        Raw claims dataset.

    vehicles
        Raw vehicles dataset.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Cleaned contracts, claims, and vehicles datasets.
    """
    contracts_clean = clean_contracts(contracts)
    claims_clean = clean_claims(claims)
    vehicles_clean = clean_vehicles(vehicles)

    return (
        contracts_clean,
        claims_clean,
        vehicles_clean,
    )