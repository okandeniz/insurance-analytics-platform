from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import (
    ClaimSeverityRequest,
    ClaimSeverityResponse,
)
from backend.services.prediction_service import (
    ClaimSeverityService,
)


app = FastAPI(
    title="Insurance Analytics API",
    description=(
        "API for post-claim damage severity estimation."
    ),
    version="1.0.0",
)

allowed_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


severity_service = ClaimSeverityService()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model": "claim_severity_pipeline",
    }


@app.post(
    "/predict",
    response_model=ClaimSeverityResponse,
)
def predict_claim_severity(
    request: ClaimSeverityRequest,
):
    try:
        prediction = severity_service.predict(
            request.model_dump()
        )

        return ClaimSeverityResponse(
            predicted_damage_amount=round(
                prediction,
                2,
            ),
            model_name=(
                "Random Forest - "
                "Log Target Severity Model"
            ),
            usage=(
                "Post-claim triage and "
                "reserve support"
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc