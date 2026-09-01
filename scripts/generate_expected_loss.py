from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyodbc


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

SPLIT_PATH = (
    DATA_DIR
    / "occurrence_split_map.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "expected_loss_summary.json"
)

CONTRACT_OUTPUT_PATH = (
    OUTPUT_DIR
    / "expected_loss_contracts.csv"
)


def load_occurrence_data() -> pd.DataFrame:
    conn = pyodbc.connect(
        "DSN=InsuranceAnalytics;",
        autocommit=True,
    )

    query = """
    SELECT *
    FROM vw_auto_claim_occurrence_ml
    """

    try:
        df = pd.read_sql(
            query,
            conn,
        )
    finally:
        conn.close()

    return df


def load_severity_data() -> pd.DataFrame:
    conn = pyodbc.connect(
        "DSN=InsuranceAnalytics;",
        autocommit=True,
    )

    query = """
    SELECT
        contract_id,
        damage_amount
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


def generate_expected_loss() -> None:

    print("Loading datasets...")

    occurrence_df = load_occurrence_data()
    severity_df = load_severity_data()

    split_df = pd.read_csv(
        SPLIT_PATH,
        dtype={"contract_id": "string"},
    )

    # ---------------------------------
    # Attach train-test split
    # ---------------------------------

    population = occurrence_df.merge(
        split_df,
        on="contract_id",
        how="inner",
        validate="one_to_one",
    )

    # ---------------------------------
    # Actual contract loss
    # ---------------------------------

    population = population.merge(
        severity_df,
        on="contract_id",
        how="left",
        validate="one_to_one",
    )

    population["actual_loss"] = (
        population["damage_amount"]
        .fillna(0)
    )

    # ---------------------------------
    # Training benchmark
    # ---------------------------------

    train_df = population[
        population["dataset"] == "Train"
    ].copy()

    test_df = population[
        population["dataset"] == "Test"
    ].copy()

    train_claim_rate = (
        train_df["has_claim"].mean()
    )

    train_mean_severity = (
        train_df.loc[
            train_df["has_claim"] == 1,
            "actual_loss",
        ].mean()
    )

    expected_loss_per_contract = (
        train_claim_rate
        * train_mean_severity
    )

    # ---------------------------------
    # Apply benchmark
    # ---------------------------------

    population["expected_loss"] = (
        expected_loss_per_contract
    )

    test_predicted_total = (
        expected_loss_per_contract
        * len(test_df)
    )

    test_actual_total = (
        test_df["actual_loss"].sum()
    )

    percentage_error = (
        (
            test_predicted_total
            - test_actual_total
        )
        / test_actual_total
        * 100
    )

    actual_to_expected = (
        test_actual_total
        / test_predicted_total
    )

    # ---------------------------------
    # Save outputs
    # ---------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    contract_output = population[
        [
            "contract_id",
            "dataset",
            "has_claim",
            "expected_loss",
            "actual_loss",
        ]
    ].copy()

    contract_output.to_csv(
        CONTRACT_OUTPUT_PATH,
        index=False,
    )

    print("Saving Expected Loss results to MySQL...")

    save_expected_loss_to_mysql(contract_output)

    print(
        "MySQL table updated:",
        "expected_loss_results",
    )

    summary = {
        "train_contracts": int(len(train_df)),
        "train_claims": int(
            train_df["has_claim"].sum()
        ),
        "train_claim_rate": float(
            train_claim_rate
        ),
        "train_mean_severity": float(
            train_mean_severity
        ),
        "expected_loss_per_contract": float(
            expected_loss_per_contract
        ),
        "test_contracts": int(len(test_df)),
        "test_claims": int(
            test_df["has_claim"].sum()
        ),
        "predicted_total_loss": float(
            test_predicted_total
        ),
        "actual_total_loss": float(
            test_actual_total
        ),
        "absolute_percentage_error_pct": float(
            abs(percentage_error)
        ),
        "actual_to_expected_ratio": float(
            actual_to_expected
        ),
    }

    with open(
        SUMMARY_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=4,
        )

    print("\nExpected Loss generated.")

    print(
        "Expected Loss per contract:",
        round(
            expected_loss_per_contract,
            2,
        ),
    )

    print(
        "Test predicted total:",
        round(
            test_predicted_total,
            2,
        ),
    )

    print(
        "Test actual total:",
        round(
            test_actual_total,
            2,
        ),
    )

    print(
        "Absolute percentage error:",
        f"{abs(percentage_error):.2f}%",
    )

    print(
        "A/E ratio:",
        round(
            actual_to_expected,
            4,
        ),
    )

    print(
        "\nContract output saved:",
        CONTRACT_OUTPUT_PATH,
    )

    print(
        "Summary saved:",
        SUMMARY_PATH,
    )

def save_expected_loss_to_mysql(
    contract_output: pd.DataFrame,
) -> None:
    """
    Replace the Expected Loss result table
    with the latest generated results.
    """

    conn = pyodbc.connect(
        "DSN=InsuranceAnalytics;",
        autocommit=False,
    )

    cursor = conn.cursor()

    try:
        # The table is fully regenerated
        # on every run.
        cursor.execute(
            "DELETE FROM expected_loss_results"
        )

        insert_query = """
        INSERT INTO expected_loss_results (
            contract_id,
            dataset,
            has_claim,
            expected_loss,
            actual_loss
        )
        VALUES (?, ?, ?, ?, ?)
        """

        rows = [
            (
                str(row.contract_id),
                str(row.dataset),
                int(row.has_claim),
                round(float(row.expected_loss), 4),
                round(float(row.actual_loss), 2),
            )
            for row in contract_output.itertuples(
                index=False
            )
        ]

        cursor.fast_executemany = True

        cursor.executemany(
            insert_query,
            rows,
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    generate_expected_loss()