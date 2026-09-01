USE insurance_analytics;

CREATE OR REPLACE VIEW vw_auto_claim_occurrence_ml AS

WITH observation AS (
    SELECT
        MAX(occurrence_date) AS observation_cutoff
    FROM claims
),

claim_check AS (
    SELECT
        ct.contract_id,

        SUM(
            CASE
                WHEN c.claim_id IS NOT NULL
                 AND c.occurrence_date >= ct.start_date
                 AND c.occurrence_date <= ct.end_date
                THEN 1
                ELSE 0
            END
        ) AS valid_claim_count,

        SUM(
            CASE
                WHEN c.claim_id IS NOT NULL
                 AND (
                        c.occurrence_date < ct.start_date
                     OR c.occurrence_date > ct.end_date
                 )
                THEN 1
                ELSE 0
            END
        ) AS invalid_claim_count

    FROM contracts AS ct

    LEFT JOIN claims AS c
        ON ct.contract_id = c.contract_id

    WHERE ct.product = 'Auto'

    GROUP BY ct.contract_id
)

SELECT
    ct.contract_id,

    ct.start_date,
    ct.end_date,

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

    CASE
        WHEN cc.valid_claim_count > 0 THEN 1
        ELSE 0
    END AS has_claim

FROM contracts AS ct

INNER JOIN vehicles AS v
    ON ct.contract_id = v.contract_id

INNER JOIN claim_check AS cc
    ON ct.contract_id = cc.contract_id

CROSS JOIN observation AS o

WHERE ct.product = 'Auto'

  -- Contract dates must be known
  AND ct.start_date IS NOT NULL
  AND ct.end_date IS NOT NULL

  -- Full contract period must be observed
  AND ct.end_date <= o.observation_cutoff

  -- Exclude contracts with inconsistent claim dates
  AND cc.invalid_claim_count = 0;
  
-- Control
SELECT
    COUNT(*) AS contracts,
    SUM(has_claim) AS claims,
    ROUND(AVG(has_claim) * 100, 2) AS claim_rate_pct
FROM vw_auto_claim_occurrence_ml;



        