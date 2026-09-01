-- ============================================================
-- Insurance Analytics Platform
-- Data Validation
-- ============================================================

USE insurance_analytics;

-- ============================================================
-- 1. ROW COUNTS
-- ============================================================

SELECT
    'contracts' AS table_name,
    COUNT(*) AS row_count
FROM contracts

UNION ALL

SELECT
    'claims',
    COUNT(*)
FROM claims

UNION ALL

SELECT
    'vehicles',
    COUNT(*)
FROM vehicles;

-- ============================================================
-- 2. PRIMARY KEY VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT contract_id) AS unique_contract_ids
FROM contracts;

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT claim_id) AS unique_claim_ids
FROM claims;

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT contract_id) AS unique_vehicle_contract_ids
FROM vehicles;

-- ============================================================
-- 3. REFERENTIAL INTEGRITY
-- ============================================================

SELECT
    COUNT(*) AS orphan_claims
FROM claims c
LEFT JOIN contracts ct
    ON c.contract_id = ct.contract_id
WHERE ct.contract_id IS NULL;


SELECT
    COUNT(*) AS orphan_vehicles
FROM vehicles v
LEFT JOIN contracts ct
    ON v.contract_id = ct.contract_id
WHERE ct.contract_id IS NULL;

-- ============================================================
-- 4. DATE VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS invalid_contract_dates
FROM contracts
WHERE
    start_date IS NOT NULL
    AND end_date IS NOT NULL
    AND end_date < start_date;

SELECT
    COUNT(*) AS invalid_claim_dates
FROM claims
WHERE
    declaration_date IS NOT NULL
    AND declaration_date < occurrence_date;

SELECT
    COUNT(*) AS invalid_claim_lags
FROM claims
WHERE
    declaration_lag_days IS NOT NULL
    AND declaration_lag_days NOT BETWEEN 0 AND 62;

-- ============================================================
-- 5. NULL VALIDATION
-- ============================================================

SELECT
    SUM(client_age IS NULL) AS missing_client_age,
    SUM(csp IS NULL) AS missing_csp,
    SUM(gender IS NULL) AS missing_gender,
    SUM(start_date IS NULL) AS missing_start_date,
    SUM(end_date IS NULL) AS missing_end_date
FROM contracts;


SELECT
    SUM(indemnified_amount IS NULL) AS missing_indemnified_amount,
    SUM(expert_id IS NULL) AS missing_expert_id,
    SUM(liability IS NULL) AS missing_liability,
    SUM(declaration_date IS NULL) AS missing_declaration_date
FROM claims;


SELECT
    SUM(year IS NULL) AS missing_year,
    SUM(power_hp IS NULL) AS missing_power,
    SUM(color IS NULL) AS missing_color,
    SUM(previous_claims IS NULL) AS missing_previous_claims
FROM vehicles;