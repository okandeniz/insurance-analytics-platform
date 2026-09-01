-- ============================================================
-- Insurance Analytics Platform
-- View: vw_contracts_enriched
--
-- Grain:
-- One row per insurance contract
--
-- Purpose:
-- Contract-level analytical dataset for Power BI and SQL analysis
-- ============================================================

USE insurance_analytics;

CREATE OR REPLACE VIEW vw_contracts_enriched AS

WITH claim_summary AS (
    SELECT
        contract_id,
        COUNT(*) AS claim_count,
        SUM(damage_amount) AS total_damage,
        SUM(indemnified_amount) AS total_indemnified
    FROM claims
    GROUP BY contract_id
),

vehicle_summary AS (
    SELECT
        contract_id,
        1 AS has_vehicle
    FROM vehicles
)

SELECT
    ct.contract_id,
    ct.client_id,
    ct.client_name,
    ct.product,

    ct.start_date,
    ct.end_date,

    CASE
        WHEN ct.start_date IS NOT NULL
         AND ct.end_date IS NOT NULL
        THEN DATEDIFF(ct.end_date, ct.start_date)
        ELSE NULL
    END AS contract_duration_days,

    ct.annual_premium,
    ct.contract_status,

    ct.city,
    ct.postal_code,
    ct.risk_zone,

    ct.client_age,

    CASE
        WHEN ct.client_age IS NULL THEN 'Unknown'
        WHEN ct.client_age < 30 THEN '18-29'
        WHEN ct.client_age < 40 THEN '30-39'
        WHEN ct.client_age < 50 THEN '40-49'
        WHEN ct.client_age < 60 THEN '50-59'
        ELSE '60+'
    END AS age_group,

    ct.channel,
    ct.csp,
    ct.gender,

    COALESCE(cs.claim_count, 0) AS claim_count,

    CASE
        WHEN COALESCE(cs.claim_count, 0) > 0
        THEN 1
        ELSE 0
    END AS has_claim,

    COALESCE(cs.total_damage, 0) AS total_damage,

    COALESCE(cs.total_indemnified, 0)
        AS total_indemnified,

    COALESCE(vs.has_vehicle, 0) AS has_vehicle

FROM contracts AS ct

LEFT JOIN claim_summary AS cs
    ON ct.contract_id = cs.contract_id

LEFT JOIN vehicle_summary AS vs
    ON ct.contract_id = vs.contract_id;
    

SELECT COUNT(*) AS row_count
FROM vw_contracts_enriched;

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT contract_id) AS unique_contracts
FROM vw_contracts_enriched;

SELECT
    SUM(claim_count) AS total_claims,
    SUM(has_claim) AS contracts_with_claims
FROM vw_contracts_enriched;

SELECT *
FROM vw_contracts_enriched
LIMIT 10;