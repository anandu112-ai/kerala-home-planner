from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Kerala Home Planner API"
    API_VERSION: str = "v1"

    # ML Model Path
    # Change this only if your model file location is different
    MODEL_PATH: str = "models/kerala_house_cost_model.pkl"

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()