from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import PredictionRequest
from app.predictor import predictor

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
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
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

    try:

        data = request.model_dump()

        predicted_cost = predictor.predict(data)

        response = {
            "predicted_cost": predicted_cost,

            "cost_range": calculate_cost_range(predicted_cost),

            "model_accuracy": 96.0,

            "cost_per_sqft": cost_per_sqft(
                predicted_cost,
                data["built_up_area_sqft"]
            ),

            "house_category": house_category(
                predicted_cost
            ),

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

            "stage_breakdown": stage_breakdown(
                predicted_cost
            ),

            "recommendations": recommendations(
                data,
                predicted_cost
            ),

            "addons": addon_summary(
                data["addons"]
            )

        }

        return response

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )