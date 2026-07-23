import logging
from app.predictor import predictor as ml_predictor
from app.services.llm_feature_extractor import extract_features
from app.services.price_adjustment import calculate_adjustments

logger = logging.getLogger("kerala_home_planner.services.predictor")

def predict_with_ai_adjustments(data: dict) -> dict:
    """
    Predicts base cost using the existing ML model, extracts site features from 
    site_description, and applies the price adjustments.
    
    If the LLM feature extraction fails or is unavailable, it returns the base ML prediction.
    """
    # 1. Run base ML prediction
    try:
        base_prediction = ml_predictor.predict(data)
    except Exception as e:
        logger.error(f"Base ML model prediction failed: {e}", exc_info=True)
        # If the base model fails, we cannot proceed, so we raise the exception
        raise e

    # 2. Extract site description
    site_description = data.get("site_description", "")
    
    # 3. If site_description is empty or LLM fails, return base prediction with no adjustment
    if not site_description.strip():
        return {
            "base_prediction": base_prediction,
            "site_adjustment_amount": 0.0,
            "site_adjustment_percentage": 0.0,
            "final_prediction": base_prediction,
            "detected_conditions": []
        }

    try:
        # Extract features using LLM
        features = extract_features(site_description)
        
        # Calculate adjustments
        adjustments = calculate_adjustments(base_prediction, features)
        return adjustments
    except Exception as e:
        logger.error(f"AI adjustment layer failed: {e}", exc_info=True)
        # Fallback to normal ML prediction normally without crashing
        return {
            "base_prediction": base_prediction,
            "site_adjustment_amount": 0.0,
            "site_adjustment_percentage": 0.0,
            "final_prediction": base_prediction,
            "detected_conditions": []
        }
