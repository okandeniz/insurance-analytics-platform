-- ============================================================
-- Insurance Analytics Platform
-- View: vw_auto_risk
--
-- Grain:
-- One row per vehicle / Auto contract
--
-- Purpose:
-- Auto insurance risk analysis for Power BI and
-- downstream machine-learning dataset preparation
-- ============================================================

USE insurance_analytics;

CREATE OR REPLACE VIEW vw_auto_risk AS

WITH claim_summary AS (
    SELECT
        contract_id,

        COUNT(*) AS claim_count,

        SUM(damage_amount) AS total_damage,

        SUM(indemnified_amount) AS total_indemnified

    FROM claims

    GROUP BY contract_id
)

SELECT
	-- Contract identifiers
    ct.contract_id,
    ct.client_id,
    -- Contract attributes
    ct.start_date,
    ct.end_date,
    
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
    
    -- Vehicle attributes
    v.brand,
    v.model,
    v.year,
    v.power_hp,
    v.power_unit,
    v.fuel_type,
    v.current_value,
    v.color,
    v.vehicle_usage,
    v.previous_claims,
    
    -- Claim summary
    
    COALESCE(cs.claim_count, 0) AS claim_count,
    
    CASE
        WHEN COALESCE(cs.claim_count, 0) > 0
        THEN 1
        ELSE 0
    END AS has_claim,
    
    COALESCE(
        cs.total_damage,
        0
    ) AS total_damage,
    
    COALESCE(
        cs.total_indemnified,
        0
    ) AS total_indemnified
    
FROM contracts AS ct
INNER JOIN vehicles AS v
    ON ct.contract_id = v.contract_id
LEFT JOIN claim_summary AS cs
    ON ct.contract_id = cs.contract_id
WHERE ct.product = 'Auto';
    

SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT contract_id) AS unique_contracts
FROM vw_auto_risk;

SELECT
    SUM(claim_count) AS total_claims,
    SUM(has_claim) AS contracts_with_claims
FROM vw_auto_risk;


SELECT
    COUNT(*) AS non_auto_records
FROM vw_auto_risk AS ar

LEFT JOIN contracts AS ct
    ON ar.contract_id = ct.contract_id

WHERE ct.product <> 'Auto';

SELECT *
FROM vw_auto_risk
LIMIT 10;