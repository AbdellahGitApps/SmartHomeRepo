from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):

    DATABASE_PATH: Path = BASE_DIR / "database" / "smart_home_edge.db"

    STORAGE_DIR: Path = BASE_DIR / "ai" / "storage"

    FACE_STORAGE_DIR: Path = STORAGE_DIR / "face"
    FACE_MODELS_DIR: Path = FACE_STORAGE_DIR / "models"
    FACE_ONNX_PATH: Path = FACE_MODELS_DIR / "arcface.onnx"

    ENERGY_STORAGE_DIR: Path = STORAGE_DIR / "energy"
    ENERGY_DATASETS_DIR: Path = ENERGY_STORAGE_DIR / "datasets"
    ENERGY_MODELS_DIR: Path = ENERGY_STORAGE_DIR / "models"

    ENERGY_MODEL_PATH: Path = ENERGY_MODELS_DIR / "energy_forecast_model.pkl"
    ENERGY_FEATURES_PATH: Path = ENERGY_MODELS_DIR / "energy_feature_columns.json"

    SIM_THRESHOLD: float = 0.60
    ADMIN_TOKEN: str = "change-me-strong-token"

    KNOWN_COOLDOWN_SEC: int = 5
    UNKNOWN_COOLDOWN_SEC: int = 10
    UNKNOWN_CONFIRM_COUNT: int = 3

    class Config:
        env_file = ".env"


settings = Settings()