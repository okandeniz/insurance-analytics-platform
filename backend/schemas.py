from pydantic import BaseModel, Field


class ClaimSeverityRequest(BaseModel):
    occurrence_date: str

    claim_type: str
    risk_zone: str
    channel: str
    csp: str | None = None
    gender: str | None = None

    brand: str
    fuel_type: str
    vehicle_usage: str

    annual_premium: float = Field(gt=0)
    client_age: float | None = Field(
        default=None,
        ge=18,
    )
    power_hp: float | None = Field(
        default=None,
        gt=0,
    )
    vehicle_age_at_claim: float | None = Field(
        default=None,
        ge=0,
    )
    current_value: float = Field(gt=0)

    previous_claims: int | None = Field(
        default=None,
        ge=0,
    )

    declaration_lag_days: float | None = Field(
        default=None,
        ge=0,
    )


class ClaimSeverityResponse(BaseModel):
    predicted_damage_amount: float
    model_name: str
    usage: str