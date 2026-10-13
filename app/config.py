import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("kokoro.config")

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)
else:
    logger.warning("[Kokoro Security Warning] .env file not found at %s. Falling back to environment variables.", _env_path)

class Config:
    APP_VERSION: str = "v1.7.7"
    BASE_DIR: Path = BASE_DIR
    PORT: int = int(os.getenv("PORT", "5050"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # PostgreSQL Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "kokoro_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # Security & Auth
    _secret = os.getenv("SECRET_KEY")
    if not _secret:
        if os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod"):
            raise RuntimeError("CRITICAL SECURITY ERROR: SECRET_KEY environment variable is mandatory in production!")
        logger.warning("[Kokoro Security Warning] SECRET_KEY not configured! Using default development key.")
        _secret = "kokoro_sakura_healing_pastel_secret_key_2026"
    SECRET_KEY: str = _secret
    MOCK_AUTH: bool = os.getenv("MOCK_AUTH", "True").lower() in ("true", "1", "yes")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # Media Storage
    UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")

# Ensure upload directories exist
Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(Config.UPLOAD_DIR / "originals").mkdir(parents=True, exist_ok=True)
(Config.UPLOAD_DIR / "thumbnails").mkdir(parents=True, exist_ok=True)
