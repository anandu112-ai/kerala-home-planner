import logging
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

logger = logging.getLogger("kerala_home_planner")

from app.config import settings
from app.schemas import PredictionRequest
from app.predictor import predictor

from app.services.predictor import predict_with_ai_adjustments
from app.services.property_comparator import find_similar_properties

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
    allow_origin_regex=r"https://.*\.(lovable\.app|lovableproject\.com|vercel\.app)$",
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
# Prediction Cache & Endpoint
# -----------------------------

PREDICTION_CACHE = {}

@app.post("/predict")
def predict(request: PredictionRequest):
    """
    Accepts property details and an optional site_description.

    Pipeline:
      1. Run existing ML model → base_prediction
      2. If site_description is provided, call LLM to extract site conditions
         and compute price adjustment.
      3. Find similar properties from dataset using similarity search.
      4. Calculate market average, min, max, and position stats.
      5. Generate an AI explanation report.
      6. Cache the prediction inputs and computed outputs for PDF report retrieval.
    """

    try:
        data = request.model_dump()

        # ---- AI pipeline (includes base ML + optional site adjustment) ----
        ai_result = predict_with_ai_adjustments(data)

        # The base ML cost is the base_prediction from the AI pipeline
        predicted_cost = ai_result["base_prediction"]
        final_prediction = ai_result.get("final_prediction", predicted_cost)
        detected_conditions = ai_result.get("detected_conditions", [])

        # ---- Similar properties search ----
        comp_result = find_similar_properties(data, final_prediction, adjustments=detected_conditions)

        # ---- Cache prediction context for PDF report generation ----
        prediction_id = str(uuid.uuid4())
        PREDICTION_CACHE[prediction_id] = {
            "property_details": data,
            "prediction_result": {
                "predicted_price": final_prediction,
                "base_prediction": predicted_cost,
                "site_adjustment_amount": ai_result.get("site_adjustment_amount", 0.0),
                "site_adjustment_percentage": ai_result.get("site_adjustment_percentage", 0.0),
                "final_prediction": final_prediction
            },
            "adjustments": detected_conditions,
            "similar_properties": comp_result["similar_properties"],
            "market_analysis": comp_result["market_analysis"],
            "ai_explanation": comp_result["ai_explanation"]
        }

        # Build the core planner response
        response = {
            "predicted_cost": predicted_cost,
            "predicted_price": final_prediction,
            "prediction_id": prediction_id,

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
            
            # Similar Properties & Market Analysis
            "similar_properties": comp_result["similar_properties"],
            "market_analysis": comp_result["market_analysis"],
            "ai_explanation": comp_result["ai_explanation"]
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
                "corrected_text": ai_result.get("corrected_text", ""),
                "detected_features": ai_result.get("detected_features", {}),
                "adjustments": ai_result.get("adjustments", []),
            }

        response["site_analysis"] = site_analysis

        return response

    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to compute prediction"
        )


@app.get("/api/v1/report/{prediction_id}")
def download_report(prediction_id: str):
    """
    Generates a professional 5-page AI Valuation Report PDF.
    Returns the file as a StreamingResponse.
    """
    if prediction_id not in PREDICTION_CACHE:
        raise HTTPException(
            status_code=404,
            detail="Report not found or expired. Please run prediction again."
        )

    cache_data = PREDICTION_CACHE[prediction_id]

    try:
        from app.services.pdf_report_generator import generate_pdf_report
        pdf_bytes = generate_pdf_report(
            property_details=cache_data["property_details"],
            prediction_result=cache_data["prediction_result"],
            adjustments=cache_data["adjustments"],
            similar_properties=cache_data["similar_properties"],
            market_analysis=cache_data["market_analysis"],
            ai_explanation=cache_data["ai_explanation"]
        )

        from io import BytesIO
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=kerala_ai_valuation_report_{prediction_id}.pdf"
            }
        )
    except Exception as e:
        logger.exception("Report generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )
