"""
predictor.py — Optimised prediction service.

Key change: ML model inference and LLM feature extraction now run in **parallel
threads** so neither blocks the other. Total wall-clock time is dominated by the
slower of the two (usually the LLM), not their sum.
"""
import logging
import concurrent.futures
from app.predictor import predictor as ml_predictor
from app.services.llm_feature_extractor import extract_features
from app.services.price_adjustment import calculate_adjustments

logger = logging.getLogger("kerala_home_planner.services.predictor")

# Single shared thread-pool — avoids creating a new pool per request
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="pred")


def predict_with_ai_adjustments(data: dict) -> dict:
    """
    Predicts base cost (ML model) and extracts LLM site features in parallel.

    Timeline (old):   ML ─── LLM_normalize ─── LLM_extract ─── done
    Timeline (new):   ML ─────────────────────────────────────┐
                            LLM_combined (one call) ──────────┤ → done
    """
    site_description = (data.get("site_description") or "").strip()

    if site_description:
        # ── Run ML and LLM concurrently ──
        ml_future  = _executor.submit(ml_predictor.predict, data)
        llm_future = _executor.submit(extract_features, site_description)

        try:
            base_prediction = ml_future.result()
        except Exception as e:
            logger.error("Base ML model prediction failed: %s", e, exc_info=True)
            raise

        try:
            features = llm_future.result()
            adjustments = calculate_adjustments(base_prediction, features)
            return adjustments
        except Exception as e:
            logger.error("AI adjustment layer failed (parallel): %s — falling back", e)
            return _no_adjustment(base_prediction)

    else:
        # ── No site description — ML only, no LLM call at all ──
        try:
            base_prediction = ml_predictor.predict(data)
        except Exception as e:
            logger.error("Base ML model prediction failed: %s", e, exc_info=True)
            raise
        return _no_adjustment(base_prediction)


def _no_adjustment(base_prediction: float) -> dict:
    return {
        "base_prediction": base_prediction,
        "site_adjustment_amount": 0.0,
        "site_adjustment_percentage": 0.0,
        "final_prediction": base_prediction,
        "detected_conditions": []
    }
