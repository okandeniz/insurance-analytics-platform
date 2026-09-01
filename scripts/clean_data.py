"""
Run the complete data-cleaning pipeline for the
Insurance Analytics Platform.

Pipeline
--------
data/raw
    ↓
src.preprocessing.cleaning
    ↓
data/processed
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.preprocessing.cleaning import clean_all_datasets


RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

CONTRACTS_RAW_PATH = RAW_DATA_DIR / "contracts.csv"
CLAIMS_RAW_PATH = RAW_DATA_DIR / "claims.csv"
VEHICLES_RAW_PATH = RAW_DATA_DIR / "vehicles.csv"

CONTRACTS_CLEAN_PATH = PROCESSED_DATA_DIR / "contracts_clean.csv"
CLAIMS_CLEAN_PATH = PROCESSED_DATA_DIR / "claims_clean.csv"
VEHICLES_CLEAN_PATH = PROCESSED_DATA_DIR / "vehicles_clean.csv"

def load_raw_datasets() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Load raw insurance datasets from disk."""

    contracts = pd.read_csv(CONTRACTS_RAW_PATH)
    claims = pd.read_csv(CLAIMS_RAW_PATH)
    vehicles = pd.read_csv(VEHICLES_RAW_PATH)

    return contracts, claims, vehicles

def export_clean_datasets(
    contracts: pd.DataFrame,
    claims: pd.DataFrame,
    vehicles: pd.DataFrame,
) -> None:
    """Export cleaned datasets to data/processed."""

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    contracts.to_csv(
        CONTRACTS_CLEAN_PATH,
        index=False,
        date_format="%Y-%m-%d",
    )

    claims.to_csv(
        CLAIMS_CLEAN_PATH,
        index=False,
        date_format="%Y-%m-%d",
    )

    vehicles.to_csv(
        VEHICLES_CLEAN_PATH,
        index=False,
    )


def validate_clean_datasets(
    contracts: pd.DataFrame,
    claims: pd.DataFrame,
    vehicles: pd.DataFrame,
) -> None:
    """Run critical structural validations."""

    # Primary keys
    assert contracts["contract_id"].notna().all()
    assert contracts["contract_id"].is_unique

    assert claims["claim_id"].notna().all()
    assert claims["claim_id"].is_unique

    assert vehicles["contract_id"].notna().all()
    assert vehicles["contract_id"].is_unique

    # Referential integrity
    contract_ids = set(contracts["contract_id"])

    assert claims["contract_id"].isin(
        contract_ids
    ).all()

    assert vehicles["contract_id"].isin(
        contract_ids
    ).all()

    # Contract dates
    contract_date_mask = (
        contracts["start_date"].notna()
        & contracts["end_date"].notna()
    )

    assert (
        contracts.loc[
            contract_date_mask,
            "end_date",
        ]
        >= contracts.loc[
            contract_date_mask,
            "start_date",
        ]
    ).all()

    # Claim dates
    claim_date_mask = (
        claims["occurrence_date"].notna()
        & claims["declaration_date"].notna()
    )

    assert (
        claims.loc[
            claim_date_mask,
            "declaration_date",
        ]
        >= claims.loc[
            claim_date_mask,
            "occurrence_date",
        ]
    ).all()

    # Claim lag
    assert (
        claims["declaration_lag_days"]
        .dropna()
        .between(0, 62)
        .all()
    )

def main() -> None:
    """Execute the complete cleaning pipeline."""

    print("Starting data-cleaning pipeline...")
    print(f"Project root: {PROJECT_ROOT}")

    # ---------------------------------------------------------
    # Load
    # ---------------------------------------------------------

    contracts_raw, claims_raw, vehicles_raw = (
        load_raw_datasets()
    )

    print("\nRaw datasets loaded:")
    print(f"Contracts: {contracts_raw.shape}")
    print(f"Claims:    {claims_raw.shape}")
    print(f"Vehicles:  {vehicles_raw.shape}")

    # ---------------------------------------------------------
    # Clean
    # ---------------------------------------------------------

    (
        contracts_clean,
        claims_clean,
        vehicles_clean,
    ) = clean_all_datasets(
        contracts_raw,
        claims_raw,
        vehicles_raw,
    )

    print("\nCleaning completed:")
    print(f"Contracts: {contracts_clean.shape}")
    print(f"Claims:    {claims_clean.shape}")
    print(f"Vehicles:  {vehicles_clean.shape}")

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    validate_clean_datasets(
        contracts_clean,
        claims_clean,
        vehicles_clean,
    )

    print("\nValidation passed.")

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    export_clean_datasets(
        contracts_clean,
        claims_clean,
        vehicles_clean,
    )

    print("\nCleaned datasets exported:")
    print(f"- {CONTRACTS_CLEAN_PATH}")
    print(f"- {CLAIMS_CLEAN_PATH}")
    print(f"- {VEHICLES_CLEAN_PATH}")

    print("\nData-cleaning pipeline completed successfully.")


if __name__ == "__main__":
    main()