"""
services/predictor.py
---------------------
Loads the scikit-learn regression model and runs base price prediction.
Model is NOT modified or retrained here.
"""

import os
import logging
import joblib
import pandas as pd

logger = logging.getLogger("kerala_house_backend.predictor")

# ── Model path resolution ──────────────────────────────────────────────────
# Default: models/house_model.pkl  (relative to working directory, which is
# /app inside the Docker container / Cloud Run instance).
# Override with MODEL_PATH environment variable if needed.
_MODEL_PATH = os.getenv("MODEL_PATH", "models/house_model.pkl")


class HouseCostPredictor:
    """Singleton wrapper around the scikit-learn pipeline."""

    def __init__(self) -> None:
        self.model = None
        self._load()

    def _load(self) -> None:
        candidates = [
            _MODEL_PATH,
            os.path.join(os.path.dirname(__file__), "..", _MODEL_PATH),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)

        if path is None:
            logger.error(
                "Model file not found. Tried: %s",
                ", ".join(os.path.abspath(p) for p in candidates),
            )
            return

        logger.info("Loading model from: %s", os.path.abspath(path))
        try:
            loaded = joblib.load(path)
            # Support both direct pipeline and dict-wrapped saves
            if isinstance(loaded, dict):
                if "model" not in loaded:
                    raise ValueError("Dict model missing 'model' key")
                loaded = loaded["model"]
            if not hasattr(loaded, "predict"):
                raise TypeError("Loaded object has no .predict() method")
            self.model = loaded
            logger.info("Model loaded successfully: %s", type(self.model).__name__)
        except Exception as exc:
            logger.error("Failed to load model: %s", exc, exc_info=True)

    def predict(self, data: dict) -> float:
        if self.model is None:
            raise RuntimeError("ML model is not loaded.")

        input_df = pd.DataFrame(
            [
                {
                    "district":           data["district"],
                    "built_up_area_sqft": data["built_up_area_sqft"],
                    "plot_size_cents":    data["plot_size_cents"],
                    "bedrooms":           data["bedrooms"],
                    "bathrooms":          data["bathrooms"],
                    "floors":             data["floors"],
                    "parking_spaces":     data["parking_spaces"],
                    "balconies":          data["balconies"],
                    "kitchen_type":       data["kitchen_type"],
                    "quality":            data["quality"],
                    "roof_type":          data["roof_type"],
                    "flooring":           data["flooring"],
                }
            ]
        )

        prediction = self.model.predict(input_df)[0]
        return round(float(prediction), 2)


# Module-level singleton — loaded once at startup
predictor = HouseCostPredictor()
