import joblib
import pandas as pd
from app.config import settings


class HouseCostPredictor:
    def __init__(self):
        try:
            self.model = joblib.load(settings.MODEL_PATH)
            print("✅ House Model Loaded Successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.model = None

    def predict(self, data: dict) -> float:
        """
        Predict construction cost using the trained ML pipeline.
        """

        if self.model is None:
            raise Exception("Model not loaded.")

        input_df = pd.DataFrame([{
            "district": data["district"],
            "built_up_area_sqft": data["built_up_area_sqft"],
            "plot_size_cents": data["plot_size_cents"],
            "bedrooms": data["bedrooms"],
            "bathrooms": data["bathrooms"],
            "floors": data["floors"],
            "parking_spaces": data["parking_spaces"],
            "balconies": data["balconies"],
            "kitchen_type": data["kitchen_type"],
            "quality": data["quality"],
            "roof_type": data["roof_type"],
            "flooring": data["flooring"]
        }])

        prediction = self.model.predict(input_df)[0]

        return round(float(prediction), 2)


predictor = HouseCostPredictor()