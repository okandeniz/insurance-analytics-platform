USE insurance_analytics;

CREATE OR REPLACE VIEW vw_auto_claim_severity_ml AS

SELECT
    c.claim_id,
    c.contract_id,

    c.occurrence_date,
    c.declaration_date,
    c.declaration_lag_days,

    c.claim_type,

    ct.annual_premium,
    ct.city,
    ct.risk_zone,
    ct.client_age,
    ct.channel,
    ct.csp,
    ct.gender,

    v.brand,
    v.model,
    v.year,
    v.power_hp,
    v.fuel_type,
    v.current_value,
    v.color,
    v.vehicle_usage,
    v.previous_claims,

    GREATEST(
        CAST(YEAR(c.occurrence_date) AS SIGNED)
        - CAST(v.year AS SIGNED),
        0
    ) AS vehicle_age_at_claim,

    c.damage_amount

FROM claims AS c

INNER JOIN contracts AS ct
    ON c.contract_id = ct.contract_id

INNER JOIN vehicles AS v
    ON c.contract_id = v.contract_id

WHERE ct.product = 'Auto'
  AND ct.start_date IS NOT NULL
  AND ct.end_date IS NOT NULL
  AND c.occurrence_date >= ct.start_date
  AND c.occurrence_date <= ct.end_date;
  
SELECT
    COUNT(*) AS claims,
    COUNT(DISTINCT claim_id) AS unique_claims,
    MIN(vehicle_age_at_claim) AS min_vehicle_age,
    MAX(vehicle_age_at_claim) AS max_vehicle_age,
    ROUND(AVG(damage_amount), 2) AS avg_damage
FROM vw_auto_claim_severity_ml;