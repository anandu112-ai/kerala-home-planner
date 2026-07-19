from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Kerala Home Planner API"
    API_VERSION: str = "v1"

    MODEL_PATH: MODEL_PATH=House_Model.pkl

    FRONTEND_URL: str = "http://localhost:5173"

    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()