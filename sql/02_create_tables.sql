-- ============================================================
-- Insurance Analytics Platform
-- Core Table Creation
-- ============================================================

USE insurance_analytics;

-- ============================================================
-- 1. CONTRACTS
-- ============================================================

CREATE TABLE IF NOT EXISTS contracts(
    contract_id        VARCHAR(20)     NOT NULL,
    client_id          VARCHAR(20)     NOT NULL,
    client_name        VARCHAR(100)    NOT NULL,
    product            VARCHAR(20)     NOT NULL,
    start_date         DATE            NULL,
    end_date           DATE            NULL,
    annual_premium     DECIMAL(12, 2)  NOT NULL,
    contract_status    VARCHAR(20)     NOT NULL,
    city               VARCHAR(50)     NOT NULL,
    postal_code        VARCHAR(10)     NOT NULL,
    risk_zone          VARCHAR(20)     NOT NULL,
    client_age         TINYINT UNSIGNED NULL,
    channel            VARCHAR(20)     NOT NULL,
    csp                VARCHAR(30)     NULL,
    gender             VARCHAR(10)     NULL,

    CONSTRAINT pk_contracts
        PRIMARY KEY (contract_id),
    
    CONSTRAINT chk_contract_premium
        CHECK (annual_premium >= 0),

    CONSTRAINT chk_client_age
        CHECK (
            client_age IS NULL
            OR client_age BETWEEN 18 AND 100
        ),
    
    CONSTRAINT chk_contract_dates
        CHECK (
            start_date IS NULL
            OR end_date IS NULL
            OR end_date >= start_date
        )
)

ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- ============================================================
-- 2. CLAIMS
-- ============================================================

CREATE TABLE IF NOT EXISTS claims (
    claim_id               VARCHAR(20)     NOT NULL,
    contract_id            VARCHAR(20)     NOT NULL,
    occurrence_date        DATE            NOT NULL,
    declaration_date       DATE            NULL,
    claim_type             VARCHAR(30)     NOT NULL,
    damage_amount          DECIMAL(12, 2)  NOT NULL,
    indemnified_amount     DECIMAL(12, 2)  NULL,
    claim_status           VARCHAR(20)     NOT NULL,
    expert_id              VARCHAR(20)     NULL,
    liability              VARCHAR(30)     NULL,
    declaration_lag_days   TINYINT UNSIGNED NULL,
    claim_dates_swapped    BOOLEAN         NOT NULL DEFAULT FALSE,

    CONSTRAINT pk_claims
        PRIMARY KEY (claim_id),

    CONSTRAINT fk_claims_contract
        FOREIGN KEY (contract_id)
        REFERENCES contracts (contract_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_damage_amount
        CHECK (damage_amount >= 0),

    CONSTRAINT chk_indemnified_amount
        CHECK (
            indemnified_amount IS NULL
            OR indemnified_amount >= 0
        ),

    CONSTRAINT chk_claim_dates
        CHECK (
            declaration_date IS NULL
            OR declaration_date >= occurrence_date
        ),

    CONSTRAINT chk_declaration_lag
        CHECK (
            declaration_lag_days IS NULL
            OR declaration_lag_days BETWEEN 0 AND 62
        )
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

-- ============================================================
-- 3. VEHICLES
-- ============================================================

CREATE TABLE IF NOT EXISTS vehicles (
    contract_id        VARCHAR(20)      NOT NULL,
    brand              VARCHAR(30)      NOT NULL,
    model              VARCHAR(30)      NOT NULL,
    year               SMALLINT UNSIGNED NULL,
    power_hp           DECIMAL(8, 2)    NULL,
    power_unit         VARCHAR(10)      NULL,
    fuel_type          VARCHAR(20)      NOT NULL,
    current_value      DECIMAL(12, 2)   NOT NULL,
    color              VARCHAR(20)      NULL,
    vehicle_usage      VARCHAR(20)      NOT NULL,
    previous_claims    TINYINT UNSIGNED NULL,

    CONSTRAINT pk_vehicles
        PRIMARY KEY (contract_id),

    CONSTRAINT fk_vehicles_contract
        FOREIGN KEY (contract_id)
        REFERENCES contracts (contract_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_vehicle_year
        CHECK (
            year IS NULL
            OR year BETWEEN 1900 AND 2100
        ),

    CONSTRAINT chk_power_hp
        CHECK (
            power_hp IS NULL
            OR power_hp > 0
        ),

    CONSTRAINT chk_current_value
        CHECK (current_value >= 0),

    CONSTRAINT chk_previous_claims
        CHECK (
            previous_claims IS NULL
            OR previous_claims >= 0
        )
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

