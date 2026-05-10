from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DB_URL = "sqlite:///./smart_home_models.db"

STORAGE_DIR = BASE_DIR / "storage"

# ===== Face storage =====
FACE_STORAGE_DIR = STORAGE_DIR / "face"
SNAPSHOTS_DIR = FACE_STORAGE_DIR / "snapshots"
PERSONS_DIR = FACE_STORAGE_DIR / "persons"
FACE_MODELS_DIR = FACE_STORAGE_DIR / "models"
FACE_ONNX_PATH = FACE_MODELS_DIR / "arcface.onnx"

# ===== Energy storage =====
ENERGY_STORAGE_DIR = STORAGE_DIR / "energy"
ENERGY_DATASETS_DIR = ENERGY_STORAGE_DIR / "datasets"
ENERGY_MODELS_DIR = ENERGY_STORAGE_DIR / "models"

ENERGY_RAW_DATA_PATH = ENERGY_DATASETS_DIR / "household_power_consumption.txt"
ENERGY_DAILY_DATA_PATH = ENERGY_DATASETS_DIR / "daily_energy.csv"
ENERGY_MODEL_PATH = ENERGY_MODELS_DIR / "energy_forecast_model.pkl"
ENERGY_FEATURES_PATH = ENERGY_MODELS_DIR / "energy_feature_columns.json"

# ===== Face config =====
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.60"))
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me-strong-token")
KNOWN_COOLDOWN_SEC = 5
UNKNOWN_COOLDOWN_SEC = 10
UNKNOWN_CONFIRM_COUNT = 3