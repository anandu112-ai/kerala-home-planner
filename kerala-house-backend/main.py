"""
main.py — Kerala House Price Prediction API
============================================
Flat entry point compatible with Google Cloud Run.

Start locally:
    uvicorn main:app --reload

In Docker / Cloud Run:
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from services.predictor import predictor
from services.llm_feature_extractor import extract_features
from services.price_adjustment import calculate_adjustments

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("kerala_house_backend")


# ── Startup / shutdown ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Kerala House Backend starting — model loaded: %s",
        predictor.model is not None,
    )
    yield
    logger.info("Kerala House Backend shutting down.")


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Kerala House Price Prediction API",
    description=(
        "ML + LLM powered construction cost estimation for Kerala properties. "
        "Base prediction from scikit-learn regression model; "
        "optional AI site-condition analysis layer for price adjustment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS ─────────────────────────────────────────────────────────────────────
# FRONTEND_URL env var → your deployed frontend (Lovable / Vercel / Railway).
# The allow_origin_regex covers all *.lovable.app and *.lovableproject.com
# preview URLs automatically.
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if _FRONTEND_URL not in _CORS_ORIGINS:
    _CORS_ORIGINS.append(_FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.(lovable\.app|lovableproject\.com|vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    district: str
    built_up_area_sqft: float = Field(..., gt=0, description="Built-up area in sq.ft.")
    plot_size_cents: float    = Field(..., gt=0, description="Plot size in cents")
    bedrooms: int             = Field(..., ge=1)
    bathrooms: int            = Field(..., ge=1)
    floors: int               = Field(..., ge=1)
    parking_spaces: int       = Field(..., ge=0)
    balconies: int            = Field(..., ge=0)
    kitchen_type: str
    quality: str
    roof_type: str
    flooring: str
    budget: float             = Field(..., gt=0, description="User's budget in INR")
    addons: List[str]         = []
    site_description: Optional[str] = Field(
        default=None,
        description=(
            "Free-text description of site conditions. "
            "E.g. 'Hilly area, no vehicle access, beautiful valley view, 1 km from main road.'"
        ),
    )


class DetectedCondition(BaseModel):
    condition: str
    impact: float
    reason: str


class SiteAnalysis(BaseModel):
    base_prediction: float
    site_adjustment_amount: float
    site_adjustment_percentage: float
    final_prediction: float
    detected_conditions: List[DetectedCondition]


class PredictionResponse(BaseModel):
    base_prediction: float
    site_adjustment_amount: float
    site_adjustment_percentage: float
    final_prediction: float
    detected_conditions: List[DetectedCondition]
    # Additional planner fields
    model_accuracy: float
    site_analysis_available: bool


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Status"])
def root():
    return {
        "status": "running",
        "service": "Kerala House Price Prediction API",
    }


@app.get("/health", tags=["Status"])
def health():
    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
    }


@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(request: PredictionRequest):
    """
    Prediction pipeline
    -------------------
    1. Run ML regression model → base_prediction
    2. If site_description is provided:
       a. LLM extracts site condition features
       b. Price adjustment engine calculates delta
    3. Return base + adjustment + detected conditions.

    If the LLM step fails for any reason (no API key, network error, etc.)
    the endpoint returns the base prediction with zero adjustment — it never
    raises a 500 due to the AI layer.
    """
    data = request.model_dump()

    # ── Step 1: Base ML prediction ──────────────────────────────────────────
    try:
        base_prediction = predictor.predict(data)
    except Exception as exc:
        logger.exception("ML model prediction failed")
        raise HTTPException(status_code=500, detail=f"Model error: {exc}") from exc

    # ── Step 2: AI site condition analysis (optional) ───────────────────────
    site_desc = (data.get("site_description") or "").strip()
    site_analysis_available = False

    adjustment_amount = 0.0
    adjustment_pct    = 0.0
    final_prediction  = base_prediction
    detected          = []

    if site_desc:
        try:
            features = extract_features(site_desc)
            if features:
                result = calculate_adjustments(base_prediction, features)
                adjustment_amount    = result["site_adjustment_amount"]
                adjustment_pct       = result["site_adjustment_percentage"]
                final_prediction     = result["final_prediction"]
                detected             = result["detected_conditions"]
                site_analysis_available = True
        except Exception:
            logger.exception(
                "Site analysis failed — returning base prediction without adjustment"
            )

    return {
        "base_prediction":            round(base_prediction, 2),
        "site_adjustment_amount":     round(adjustment_amount, 2),
        "site_adjustment_percentage": round(adjustment_pct, 2),
        "final_prediction":           round(final_prediction, 2),
        "detected_conditions":        detected,
        "model_accuracy":             96.0,
        "site_analysis_available":    site_analysis_available,
    }
