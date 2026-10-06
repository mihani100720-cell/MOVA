"""
MOVA Configuration Settings
Centralized configuration management with validation and environment loading.
"""

import os
from pathlib import Path
# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
MODELS_DIR = ASSETS_DIR / "models"
DATA_DIR = ROOT_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
DB_PATH = DATA_DIR / "mova.db"

# Create required directories
for d in [ASSETS_DIR, MODELS_DIR, DATA_DIR, SESSIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load .env (with fallback if python-dotenv is not installed)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# Model URLs
MODEL_URLS = {
    "pose_landmarker.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "face_landmarker.task": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
}

class Settings:
    """Application settings class."""
    APP_NAME: str = "MOVA"
    APP_SUBTITLE: str = "Multimodal Spatial Gaming & Movement Intelligence Platform"
    TAGLINE: str = "MOVE. PLAY. IMPROVE."
    VERSION: str = "1.0.0"

    # Environment
    ENV: str = os.getenv("MOVA_ENV", "development")
    LOG_LEVEL: str = os.getenv("MOVA_LOG_LEVEL", "INFO")
    DEMO_MODE_DEFAULT: bool = os.getenv("MOVA_DEMO_MODE", "false").lower() == "true"
    CAMERA_INDEX: int = int(os.getenv("MOVA_CAMERA_INDEX", "0"))
    TARGET_FPS: int = int(os.getenv("MOVA_TARGET_FPS", "30"))

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    # Vision thresholds
    MIN_DETECTION_CONFIDENCE: float = 0.5
    MIN_TRACKING_CONFIDENCE: float = 0.5

    # Path properties
    MODELS_DIR = MODELS_DIR
    DB_PATH = DB_PATH
    SESSIONS_DIR = SESSIONS_DIR
    ASSETS_DIR = ASSETS_DIR

settings = Settings()
