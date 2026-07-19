import os
import joblib
import pandas as pd
from app.config import settings


class HouseCostPredictor:
    def __init__(self):
        self.model = None

        print("========== MODEL DEBUG ==========")
        print("Current Working Directory:", os.getcwd())
        print("Configured Model Path:", settings.MODEL_PATH)
        print("Absolute Path:", os.path.abspath(settings.MODEL_PATH))
        print("File Exists:", os.path.exists(settings.MODEL_PATH))

        try:
            self.model = joblib.load(settings.MODEL_PATH)
            print("✅ House Model Loaded Successfully")
            print("Model Type:", type(self.model))

        except Exception as e:
            print("❌ Failed to load model")
            print(type(e).__name__)
            print(e)

    def predict(self, data: dict) -> float:

        print("Predict called")
        print("Model object:", self.model)

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
