import os
import joblib
import pandas as pd
from app.config import settings


class HouseCostPredictor:

    def __init__(self):
        self.model = None

        # Resolve model path dynamically
        model_path = settings.MODEL_PATH
        if not os.path.exists(model_path):
            # Try resolving relative to backend directory (parent of app directory)
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate = os.path.join(backend_dir, settings.MODEL_PATH)
            if os.path.exists(candidate):
                model_path = candidate

        print("========== MODEL DEBUG ==========")
        print("Current Working Directory:", os.getcwd())
        print("Resolved Model Path:", model_path)
        print("Absolute Path:", os.path.abspath(model_path))
        print("File Exists:", os.path.exists(model_path))

        try:
            loaded_model = joblib.load(model_path)

            print("Loaded Object Type:", type(loaded_model))

            # If saved as dictionary from Colab
            if isinstance(loaded_model, dict):

                print("Dictionary Keys:", loaded_model.keys())

                if "model" in loaded_model:
                    self.model = loaded_model["model"]

                else:
                    raise Exception(
                        "Dictionary does not contain 'model' key"
                    )

            # If saved directly as sklearn pipeline/model
            else:
                self.model = loaded_model


            print("✅ House Model Loaded Successfully")
            print("Final Model Type:", type(self.model))


            # Check if model supports prediction
            if not hasattr(self.model, "predict"):
                raise Exception(
                    "Loaded object is not a valid ML model"
                )


        except Exception as e:

            print("❌ Failed to load model")
            print(type(e).__name__)
            print(e)



    def predict(self, data: dict) -> float:

        print("========== PREDICTION DEBUG ==========")

        if self.model is None:
            raise Exception("Model not loaded.")


        print("Received Data:")
        print(data)


        # Create dataframe matching training features
        input_df = pd.DataFrame([{

            "district": data["district"],

            "built_up_area_sqft":
                data["built_up_area_sqft"],

            "plot_size_cents":
                data["plot_size_cents"],

            "bedrooms":
                data["bedrooms"],

            "bathrooms":
                data["bathrooms"],

            "floors":
                data["floors"],

            "parking_spaces":
                data["parking_spaces"],

            "balconies":
                data["balconies"],

            "kitchen_type":
                data["kitchen_type"],

            "quality":
                data["quality"],

            "roof_type":
                data["roof_type"],

            "flooring":
                data["flooring"]

        }])


        print("Input DataFrame:")
        print(input_df)


        # Optional feature check
        try:
            print(
                "Expected Features:",
                self.model.feature_names_in_
            )

        except Exception:
            pass


        prediction = self.model.predict(input_df)[0]


        print("Prediction:", prediction)


        return round(float(prediction), 2)



predictor = HouseCostPredictor()
