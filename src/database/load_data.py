"""
Data loading utilities for the Insurance Analytics Platform.

This module loads cleaned datasets from data/processed
into the MySQL analytical database.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.database.connection import get_mysql_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

CONTRACTS_PATH = PROCESSED_DATA_DIR / "contracts_clean.csv"
CLAIMS_PATH = PROCESSED_DATA_DIR / "claims_clean.csv"
VEHICLES_PATH = PROCESSED_DATA_DIR / "vehicles_clean.csv"

def to_mysql_value(value):
    """
    Convert Pandas / NumPy values into MySQL-compatible values.

    Missing values are converted to None so that they are
    inserted as SQL NULL.
    """
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if isinstance(value, np.generic):
        return value.item()

    return value

def dataframe_to_records(
    df: pd.DataFrame,
) -> list[tuple]:
    """
    Convert a DataFrame into MySQL-compatible row tuples.
    """
    return [
        tuple(
            to_mysql_value(value)
            for value in row
        )
        for row in df.itertuples(
            index=False,
            name=None,
        )
    ]

def clear_core_tables() -> None:
    """
    Clear core MySQL tables before a full reload.

    Child tables are cleared before contracts because of
    foreign-key dependencies.
    """
    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM claims")
        cursor.execute("DELETE FROM vehicles")
        cursor.execute("DELETE FROM contracts")

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

def load_contracts(
    contracts: pd.DataFrame,
) -> int:
    """
    Load cleaned contract records into MySQL.

    Returns
    -------
    int
        Number of inserted records.
    """
    insert_query = """
        INSERT INTO contracts (
            contract_id,
            client_id,
            client_name,
            product,
            start_date,
            end_date,
            annual_premium,
            contract_status,
            city,
            postal_code,
            risk_zone,
            client_age,
            channel,
            csp,
            gender
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """

    records = dataframe_to_records(
        contracts
    )

    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        cursor.executemany(
            insert_query,
            records,
        )

        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

def load_processed_contracts() -> pd.DataFrame:
    """Load cleaned contracts CSV."""

    return pd.read_csv(
        CONTRACTS_PATH,
        parse_dates=[
            "start_date",
            "end_date",
        ],
    )

def load_processed_claims() -> pd.DataFrame:
    """Load cleaned claims CSV."""

    return pd.read_csv(
        CLAIMS_PATH,
        parse_dates=[
            "occurrence_date",
            "declaration_date",
        ],
    )

def load_claims(
    claims: pd.DataFrame,
) -> int:
    """Load cleaned claim records into MySQL."""

    insert_query = """
        INSERT INTO claims (
            claim_id,
            contract_id,
            occurrence_date,
            declaration_date,
            claim_type,
            damage_amount,
            indemnified_amount,
            claim_status,
            expert_id,
            liability,
            declaration_lag_days,
            claim_dates_swapped
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """

    records = dataframe_to_records(claims)

    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        cursor.executemany(
            insert_query,
            records,
        )

        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

def load_processed_vehicles() -> pd.DataFrame:
    """Load cleaned vehicles CSV."""

    return pd.read_csv(
        VEHICLES_PATH
    )

def load_vehicles(
    vehicles: pd.DataFrame,
) -> int:
    """Load cleaned vehicle records into MySQL."""

    insert_query = """
        INSERT INTO vehicles (
            contract_id,
            brand,
            model,
            year,
            power_hp,
            power_unit,
            fuel_type,
            current_value,
            color,
            vehicle_usage,
            previous_claims
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s
        )
    """

    records = dataframe_to_records(vehicles)

    connection = get_mysql_connection()
    cursor = connection.cursor()

    try:
        cursor.executemany(
            insert_query,
            records,
        )

        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

def main() -> None:
    """Load all cleaned datasets into MySQL."""

    print("Starting MySQL data load...")

    # ---------------------------------------------------------
    # Load processed CSV files
    # ---------------------------------------------------------

    contracts = load_processed_contracts()
    claims = load_processed_claims()
    vehicles = load_processed_vehicles()

    print("\nProcessed datasets loaded:")
    print(f"Contracts: {len(contracts):,}")
    print(f"Claims:    {len(claims):,}")
    print(f"Vehicles:  {len(vehicles):,}")

    # ---------------------------------------------------------
    # Reset database tables
    # ---------------------------------------------------------

    clear_core_tables()

    print("\nExisting MySQL records cleared.")

    # ---------------------------------------------------------
    # Insert data
    # ---------------------------------------------------------

    contracts_inserted = load_contracts(
        contracts
    )

    claims_inserted = load_claims(
        claims
    )

    vehicles_inserted = load_vehicles(
        vehicles
    )

    print("\nRecords inserted into MySQL:")
    print(f"Contracts: {contracts_inserted:,}")
    print(f"Claims:    {claims_inserted:,}")
    print(f"Vehicles:  {vehicles_inserted:,}")

    print("\nMySQL data load completed successfully.")


if __name__ == "__main__":
    main()