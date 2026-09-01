-- ============================================================
-- Insurance Analytics Platform
-- SQL Analysis
-- ============================================================

USE insurance_analytics;

SELECT * FROM contracts LIMIT 10;

-- ============================================================
-- 1. PORTFOLIO OVERVIEW
-- ============================================================

SELECT
	COUNT(*) AS total_contracts,
    COUNT(DISTINCT client_id) AS total_clients,
    ROUND(SUM(annual_premium), 2) AS total_annual_premium,
    ROUND(AVG(annual_premium), 2) AS avg_annual_premium
FROM contracts;

-- On a product basis

SELECT
	product,
    COUNT(*) AS contract_count,
    ROUND(
		COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(),
        2
	) AS contract_pct,
    ROUND(SUM(annual_premium), 2) AS total_premium,
    ROUND(AVG(annual_premium), 2) AS avg_premium
FROM contracts
GROUP BY product
ORDER BY contract_count DESC;

-- Contract status analysis
SELECT
    contract_status,
    COUNT(*) AS contract_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS contract_pct,
    ROUND(SUM(annual_premium), 2) AS total_premium
FROM contracts
GROUP BY contract_status
ORDER BY contract_count DESC;

-- Channel analysis
SELECT
    channel,
    COUNT(*) AS contract_count,
    ROUND(AVG(annual_premium), 2) AS avg_premium,
    ROUND(SUM(annual_premium), 2) AS total_premium
FROM contracts
GROUP BY channel
ORDER BY contract_count DESC;

-- Risk zone
SELECT
    risk_zone,
    COUNT(*) AS contract_count,
    ROUND(AVG(annual_premium), 2) AS avg_premium,
    ROUND(SUM(annual_premium), 2) AS total_premium
FROM contracts
GROUP BY risk_zone
ORDER BY contract_count DESC;

-- City-based portfolio
SELECT
    city,
    COUNT(*) AS contract_count,
    ROUND(SUM(annual_premium), 2) AS total_premium,
    ROUND(AVG(annual_premium), 2) AS avg_premium
FROM contracts
GROUP BY city
ORDER BY contract_count DESC;

-- ============================================================
-- 2. CLAIMS OVERVIEW
-- ============================================================

SELECT * FROM claims LIMIT 10;

SELECT
	COUNT(*) AS total_claims,
    ROUND(SUM(damage_amount), 2) AS total_damage_amount,
    ROUND(SUM(indemnified_amount), 2) AS total_indemnified_amount,
    ROUND(AVG(damage_amount), 2) AS avg_damage_amount,
    ROUND(
		AVG(
			CASE
				WHEN indemnified_amount IS NOT NULL
                THEN indemnified_amount
			END
		),
        2
	) AS avg_indemnified_amount
FROM claims;

-- claim status
SELECT
    claim_status,
    COUNT(*) AS claim_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS claim_pct,
    ROUND(SUM(damage_amount), 2) AS total_damage,
    ROUND(SUM(indemnified_amount), 2) AS total_indemnified
FROM claims
GROUP BY claim_status
ORDER BY claim_count DESC;

-- Claim type
SELECT
    claim_type,
    COUNT(*) AS claim_count,
    ROUND(AVG(damage_amount), 2) AS avg_damage,
    ROUND(SUM(damage_amount), 2) AS total_damage,
    ROUND(SUM(indemnified_amount), 2) AS total_indemnified
FROM claims
GROUP BY claim_type
ORDER BY claim_count DESC;

-- product-based claim frequency
SELECT * FROM contracts LIMIT 5;

SELECT * FROM claims LIMIT 5;

SELECT
	ct.product,
    
    COUNT(DISTINCT ct.contract_id) AS contract_count,
    
    COUNT(c.claim_id) AS claim_count,
    
    ROUND(
		COUNT(c.claim_id) * 100.0
        / COUNT(DISTINCT ct.contract_id),
        2
	) AS claim_frequency_pct

FROM contracts AS ct
LEFT JOIN claims AS c
	ON ct.contract_id = c.contract_id
GROUP BY ct.product
ORDER BY claim_frequency_pct DESC;

-- actual portfolio loss ratio by product
SELECT
	ct.product,
    COUNT(DISTINCT ct.contract_id) AS contract_count,
    COUNT(c.claim_id) AS claim_count,
    
    ROUND(
        SUM(ct.annual_premium),
        2
    ) AS total_premium,
    
    ROUND(
        COALESCE(SUM(c.damage_amount), 0),
        2
    ) AS total_damage,
    
    ROUND(
        COALESCE(SUM(c.indemnified_amount), 0),
        2
    ) AS total_indemnified,
    
    ROUND(
        COALESCE(SUM(c.indemnified_amount), 0)
        / NULLIF(SUM(ct.annual_premium), 0)
        * 100,
        2
    ) AS loss_ratio_pct
    
FROM contracts AS ct
LEFT JOIN claims AS c
	ON ct.contract_id = c.contract_id
GROUP BY ct.product
ORDER BY loss_ratio_pct DESC;

-- NOTE:
-- indemnified_amount is NULL for Open, In_progress, and Expert_review claims.
-- Therefore, indemnity-based loss ratios represent currently finalized/paid
-- indemnification rather than ultimate incurred loss.

-- ============================================================
-- 3. VEHICLE ANALYSIS
-- ============================================================

SELECT * FROM vehicles LIMIT 10;

-- Vehicle coverage of Auto contracts

SELECT
	COUNT(DISTINCT ct.contract_id) AS auto_contracts,
    COUNT(DISTINCT v.contract_id) AS vehicle_records,
    
    ROUND(
		COUNT(DISTINCT v.contract_id) * 100.0
        / COUNT(DISTINCT ct.contract_id),
        2
	) AS vehicle_coverage_pct
FROM contracts as ct
LEFT JOIN vehicles AS v
	ON ct.contract_id = v.contract_id
WHERE ct.product = 'Auto';

-- Brand-based risk and value profile

SELECT * FROM claims LIMIT 10;

SELECT
	v.brand,
    COUNT(*) AS vehicle_count,
    ROUND(
        AVG(v.current_value),
        2
    ) AS avg_vehicle_value,
    ROUND(
        AVG(v.power_hp),
        2
    ) AS avg_power_hp,
    COUNT(c.claim_id) AS claim_count,
    ROUND(
        COUNT(c.claim_id) * 100.0
        / COUNT(*),
        2
    ) AS claim_frequency_pct,
    ROUND(
        COALESCE(SUM(c.damage_amount), 0),
        2
    ) AS total_damage,
    ROUND(
        COALESCE(SUM(c.indemnified_amount), 0),
        2
    ) AS total_indemnified
    
FROM vehicles AS v
LEFT JOIN claims AS c
	ON v.contract_id = c.contract_id
GROUP BY v.brand
ORDER BY claim_frequency_pct DESC;

-- fuel type
SELECT
    v.fuel_type,
    COUNT(*) AS vehicle_count,
    ROUND(
        AVG(v.current_value),
        2
    ) AS avg_vehicle_value,
    ROUND(
        AVG(v.power_hp),
        2
    ) AS avg_power_hp,
    COUNT(c.claim_id) AS claim_count,
    ROUND(
        COUNT(c.claim_id) * 100.0
        / COUNT(*),
        2
    ) AS claim_frequency_pct,
    ROUND(
        AVG(c.damage_amount),
        2
    ) AS avg_claim_damage
    
FROM vehicles AS v
LEFT JOIN claims AS c
    ON v.contract_id = c.contract_id
GROUP BY v.fuel_type
ORDER BY claim_frequency_pct DESC;

-- vehicle_usage
SELECT
    v.vehicle_usage,
    COUNT(*) AS vehicle_count,
    COUNT(c.claim_id) AS claim_count,
    ROUND(
        COUNT(c.claim_id) * 100.0
        / COUNT(*),
        2
    ) AS claim_frequency_pct,
    ROUND(
        AVG(c.damage_amount),
        2
    ) AS avg_claim_damage,
    ROUND(
        COALESCE(SUM(c.indemnified_amount), 0),
        2
    ) AS total_indemnified

FROM vehicles AS v
LEFT JOIN claims AS c
    ON v.contract_id = c.contract_id
GROUP BY v.vehicle_usage
ORDER BY claim_frequency_pct DESC;

-- previous_claims
SELECT
    v.previous_claims,
    COUNT(*) AS vehicle_count,
    COUNT(c.claim_id) AS claim_count,
    ROUND(
        COUNT(c.claim_id) * 100.0
        / COUNT(*),
        2
    ) AS claim_frequency_pct,
    ROUND(
        AVG(c.damage_amount),
        2
    ) AS avg_claim_damage
    
FROM vehicles AS v
LEFT JOIN claims AS c
    ON v.contract_id = c.contract_id
WHERE v.previous_claims IS NOT NULL
GROUP BY v.previous_claims
ORDER BY v.previous_claims;

-- NOTE:
-- Claim-frequency differences across vehicle characteristics
-- should be interpreted cautiously because the number of claims
-- is relatively small and some vehicle groups have substantially
-- smaller sample sizes.

-- ============================================================
-- 4. RISK DRIVER ANALYSIS
-- ============================================================

SELECT 
	ct.risk_zone,
    COUNT(DISTINCT ct.contract_id) AS contract_count,
    COUNT(DISTINCT c.claim_id) AS claim_count,
    ROUND(
        COUNT(DISTINCT c.claim_id) * 100.0
        / COUNT(DISTINCT ct.contract_id),
        2
    ) AS claim_frequency_pct,
    ROUND(
        AVG(c.damage_amount),
        2
    ) AS avg_claim_damage,
    ROUND(
        COALESCE(SUM(c.damage_amount), 0),
        2
    ) AS total_damage
    
FROM contracts AS ct
LEFT JOIN claims AS c
	ON ct.contract_id = c.contract_id
GROUP BY ct.risk_zone
ORDER BY claim_frequency_pct DESC;

-- risk zone × Auto

SELECT
    ct.risk_zone,
    COUNT(DISTINCT ct.contract_id) AS auto_contracts,
    COUNT(DISTINCT c.claim_id) AS claim_count,
    ROUND(
        COUNT(DISTINCT c.claim_id) * 100.0
        / COUNT(DISTINCT ct.contract_id),
        2
    ) AS claim_frequency_pct,
    ROUND(
        AVG(ct.annual_premium),
        2
    ) AS avg_premium,
    ROUND(
        AVG(c.damage_amount),
        2
    ) AS avg_claim_damage

FROM contracts AS ct
LEFT JOIN claims AS c
    ON ct.contract_id = c.contract_id
WHERE ct.product = 'Auto'
GROUP BY ct.risk_zone
ORDER BY claim_frequency_pct DESC;

SELECT
    CASE
        WHEN client_age IS NULL THEN 'Unknown'
        WHEN client_age < 30 THEN '18-29'
        WHEN client_age < 40 THEN '30-39'
        WHEN client_age < 50 THEN '40-49'
        WHEN client_age < 60 THEN '50-59'
        ELSE '60+'
    END AS age_group,
    COUNT(DISTINCT ct.contract_id) AS contract_count,
    COUNT(DISTINCT c.claim_id) AS claim_count,
    ROUND(
        COUNT(DISTINCT c.claim_id) * 100.0
        / COUNT(DISTINCT ct.contract_id),
        2
    ) AS claim_frequency_pct,
    ROUND(
        AVG(c.damage_amount),
        2
    ) AS avg_claim_damage

FROM contracts AS ct
LEFT JOIN claims AS c
    ON ct.contract_id = c.contract_id
GROUP BY age_group
ORDER BY age_group;

-- NOTE:
-- Higher pricing in the High risk zone does not correspond to a
-- higher realized claim frequency in the current sample.
-- This should not be interpreted as evidence of mispricing because
-- claim volume is limited and portfolio composition differs by product.

-- ============================================================
-- 5. PREMIUM & LOSS PERFORMANCE
-- ============================================================

-- Let's create a CTE (Common Table Expression)
WITH claim_by_contract AS(
	SELECT
		contract_id,
        COUNT(*) AS claim_count,
        SUM(damage_amount) AS total_damage,
        SUM(indemnified_amount) AS total_indemnified
	FROM claims
    GROUP BY contract_id
)

SELECT
    ct.risk_zone,
    COUNT(*) AS contract_count,
    SUM(
        COALESCE(cb.claim_count, 0)
    ) AS claim_count,
    ROUND(
        SUM(ct.annual_premium),
        2
    ) AS total_premium,
    ROUND(
        COALESCE(SUM(cb.total_damage), 0),
        2
    ) AS total_damage,
    ROUND(
        COALESCE(SUM(cb.total_indemnified), 0),
        2
    ) AS total_indemnified,
    ROUND(
        COALESCE(SUM(cb.total_damage), 0)
        / NULLIF(SUM(ct.annual_premium), 0)
        * 100,
        2
    ) AS damage_ratio_pct,
    ROUND(
        COALESCE(SUM(cb.total_indemnified), 0)
        / NULLIF(SUM(ct.annual_premium), 0)
        * 100,
        2
    ) AS finalized_loss_ratio_pct

FROM contracts AS ct
LEFT JOIN claim_by_contract AS cb
    ON ct.contract_id = cb.contract_id
GROUP BY ct.risk_zone
ORDER BY finalized_loss_ratio_pct DESC;

-- vehicle_usage

WITH claim_by_contract AS (
    SELECT
        contract_id,
        COUNT(*) AS claim_count,
        SUM(damage_amount) AS total_damage,
        SUM(indemnified_amount) AS total_indemnified
    FROM claims
    GROUP BY contract_id
)

SELECT
    v.vehicle_usage,
    COUNT(*) AS vehicle_count,
    SUM(
        COALESCE(cb.claim_count, 0)
    ) AS claim_count,
    ROUND(
        SUM(ct.annual_premium),
        2
    ) AS total_premium,
    ROUND(
        COALESCE(SUM(cb.total_damage), 0),
        2
    ) AS total_damage,
    ROUND(
        COALESCE(SUM(cb.total_indemnified), 0),
        2
    ) AS total_indemnified,
    ROUND(
        COALESCE(SUM(cb.total_indemnified), 0)
        / NULLIF(SUM(ct.annual_premium), 0)
        * 100,
        2
    ) AS finalized_loss_ratio_pct

FROM vehicles AS v
INNER JOIN contracts AS ct
    ON v.contract_id = ct.contract_id
LEFT JOIN claim_by_contract AS cb
    ON v.contract_id = cb.contract_id
GROUP BY v.vehicle_usage
ORDER BY finalized_loss_ratio_pct DESC;

-- ============================================================
-- ANALYTICAL NOTES
-- ============================================================

-- 1. Low risk-zone policies show the highest realized damage
--    and finalized loss ratios in the current sample, despite
--    having lower average premiums than High risk-zone policies.
--
-- 2. Professional vehicle usage has the lowest claim frequency
--    among usage categories but the highest finalized loss ratio.
--
-- 3. Frequency and severity should therefore be analyzed
--    separately throughout the reporting and modeling stages.
--
-- 4. Finalized loss ratios reflect currently available
--    indemnification amounts and should not be interpreted as
--    ultimate incurred loss because some claims remain unsettled.
