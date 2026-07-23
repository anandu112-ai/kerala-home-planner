import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("kerala_home_planner")

from app.config import settings
from app.schemas import PredictionRequest
from app.predictor import predictor

from app.services.predictor import predict_with_ai_adjustments

from app.planner import (
    calculate_cost_range,
    cost_per_sqft,
    house_category,
    construction_time,
    budget_analysis,
    stage_breakdown,
    addon_summary,
    health_score,
    recommendations,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION
)

# -----------------------------
# CORS
# Allow the configured frontend URL plus common local dev origins.
# In production on Railway, FRONTEND_URL is set via environment variable
# so Lovable/deployed frontends are automatically included.
# -----------------------------

_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add the configured frontend URL if it's not already in the list
if settings.FRONTEND_URL and settings.FRONTEND_URL not in _cors_origins:
    _cors_origins.append(settings.FRONTEND_URL)

# Note: wildcard subdomains like *.lovable.app are handled via allow_origin_regex below,
# NOT added to allow_origins (Starlette doesn't support glob patterns in that list).

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.(lovable\.app|lovableproject\.com)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Home
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "Kerala Home Planner API is Running"
    }

# -----------------------------
# Health Check
# -----------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
        "api": settings.PROJECT_NAME,
        "version": settings.API_VERSION
    }

# -----------------------------
# Prediction Endpoint
# -----------------------------

@app.post("/predict")
def predict(request: PredictionRequest):
    """
    Accepts property details and an optional site_description.

    Pipeline:
      1. Run existing ML model → base_prediction
      2. If site_description is provided, call LLM to extract site conditions
         and compute price adjustment.
      3. Return full response including site_analysis when available.
         If the LLM step fails, the endpoint still returns the base ML prediction
         without crashing.
    """

    try:
        data = request.model_dump()

        # ---- AI pipeline (includes base ML + optional site adjustment) ----
        ai_result = predict_with_ai_adjustments(data)

        # The base ML cost is the base_prediction from the AI pipeline
        predicted_cost = ai_result["base_prediction"]

        # Build the core planner response (unchanged from original logic)
        response = {
            "predicted_cost": predicted_cost,

            "cost_range": calculate_cost_range(predicted_cost),

            "model_accuracy": 96.0,

            "cost_per_sqft": cost_per_sqft(
                predicted_cost,
                data["built_up_area_sqft"]
            ),

            "house_category": house_category(predicted_cost),

            "construction_time": construction_time(
                data["built_up_area_sqft"],
                data["floors"]
            ),

            "health_score": health_score(
                predicted_cost,
                data["budget"],
                data["floors"]
            ),

            "budget": budget_analysis(
                predicted_cost,
                data["budget"]
            ),

            "stage_breakdown": stage_breakdown(predicted_cost),

            "recommendations": recommendations(data, predicted_cost),

            "addons": addon_summary(data["addons"]),
        }

        # ---- Attach site analysis only when site_description was provided ----
        site_analysis = None
        if data.get("site_description") and data["site_description"].strip():
            site_analysis = {
                "base_prediction": ai_result["base_prediction"],
                "site_adjustment_amount": ai_result["site_adjustment_amount"],
                "site_adjustment_percentage": ai_result["site_adjustment_percentage"],
                "final_prediction": ai_result["final_prediction"],
                "detected_conditions": ai_result["detected_conditions"],
            }

        response["site_analysis"] = site_analysis

        return response

    except Exception:

        logger.exception("Prediction failed")

        raise HTTPException(
            status_code=500,
            detail="Failed to compute prediction"
        )
