-- ============================================================
-- Insurance Analytics Platform
-- View: vw_claims_enriched
--
-- Grain:
-- One row per claim
--
-- Purpose:
-- Claim-level analytical dataset for Power BI and SQL analysis
-- ============================================================

USE insurance_analytics;

CREATE OR REPLACE VIEW vw_claims_enriched AS
SELECT
	c.claim_id,
    c.contract_id,
    -- Claim dates
    c.occurrence_date,
    c.declaration_date,
    c.declaration_lag_days,
    
    YEAR(c.occurrence_date) AS occurrence_year,
    MONTH(c.occurrence_date) AS occurrence_month,
    QUARTER(c.occurrence_date) AS occurrence_quarter,
    
    -- Claim attributes
    c.claim_type,
    c.claim_status,
    c.expert_id,
    c.liability,
    c.damage_amount,
    c.indemnified_amount,
    c.claim_dates_swapped,
    
	-- Useful claim flags
    CASE
        WHEN c.claim_status = 'Closed'
        THEN 1
        ELSE 0
    END AS is_closed,
    
    CASE
        WHEN c.claim_status = 'Rejected'
        THEN 1
        ELSE 0
    END AS is_rejected,
    
   CASE
        WHEN c.indemnified_amount IS NULL
        THEN 0
        ELSE 1
    END AS has_finalized_indemnity, 
    
    CASE
        WHEN c.indemnified_amount > 0
        THEN 1
        ELSE 0
    END AS has_indemnity_payment,
    
    -- Contract context
    ct.product,
    ct.annual_premium,
    ct.contract_status,

    ct.city,
    ct.postal_code,
    ct.risk_zone,

    ct.client_age,
    ct.channel,
    ct.csp,
    ct.gender
    
FROM claims AS c
INNER JOIN contracts AS ct
	ON c.contract_id = ct.contract_id;
    
    
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT claim_id) AS unique_claims
FROM vw_claims_enriched;   

SELECT
    COUNT(*) AS orphan_claims
FROM vw_claims_enriched
WHERE contract_id IS NULL;

SELECT
    claim_status,
    COUNT(*) AS claim_count,
    SUM(is_closed) AS closed_flag_count,
    SUM(is_rejected) AS rejected_flag_count,
    SUM(has_finalized_indemnity) AS finalized_count,
    SUM(has_indemnity_payment) AS paid_count
FROM vw_claims_enriched
GROUP BY claim_status
ORDER BY claim_count DESC;

SELECT
    ROUND(SUM(damage_amount), 2) AS total_damage,
    ROUND(SUM(indemnified_amount), 2) AS total_indemnified
FROM vw_claims_enriched;