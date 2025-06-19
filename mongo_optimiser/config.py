import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env file in project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded configuration from {env_path}")
    else:
        print("⚠️  No .env file found. Using environment variables or defaults.")
except ImportError:
    print("⚠️  python-dotenv not installed. Using environment variables only.")

# MongoDB Configuration
MONGO_MODE = os.getenv("MONGO_MODE", "local")  # 'local' or 'remote'
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "testdb")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_AUTH_DB = os.getenv("MONGO_AUTH_DB", "admin")

# Docker Configuration (for local mode)
MONGO_CONTAINER_NAME = os.getenv("MONGO_CONTAINER_NAME", "mongo-optimizer")
MONGO_DOCKER_IMAGE = os.getenv("MONGO_DOCKER_IMAGE", "mongo:4.4")

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct")
OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
)

# Analysis Configuration
MIN_DURATION_MS = int(os.getenv("MIN_DURATION_MS", "100"))
MAX_QUERIES_TO_ANALYZE = int(os.getenv("MAX_QUERIES_TO_ANALYZE", "10"))


def build_mongo_uri() -> str:
    """Build MongoDB URI based on configuration."""
    if MONGO_MODE == "local":
        return "mongodb://localhost:27017/"

    # For remote mode, build URI from components
    if MONGO_USERNAME and MONGO_PASSWORD:
        auth_part = f"{MONGO_USERNAME}:{MONGO_PASSWORD}@"
        auth_params = f"?authSource={MONGO_AUTH_DB}" if MONGO_AUTH_DB else ""

        # Extract host and port from MONGO_URI if it doesn't include auth
        if "://" in MONGO_URI:
            protocol, rest = MONGO_URI.split("://", 1)
            host_part = rest.rstrip("/")
            return f"{protocol}://{auth_part}{host_part}/{auth_params}"
        else:
            return f"mongodb://{auth_part}{MONGO_URI.rstrip('/')}/{auth_params}"

    return MONGO_URI


def validate_config() -> bool:
    """Validate configuration and return True if valid."""
    errors = []

    if not OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY is required")

    if MONGO_MODE not in ["local", "remote"]:
        errors.append("MONGO_MODE must be 'local' or 'remote'")

    if MONGO_MODE == "remote" and not MONGO_URI:
        errors.append("MONGO_URI is required when MONGO_MODE=remote")

    if MIN_DURATION_MS < 0:
        errors.append("MIN_DURATION_MS must be >= 0")

    if MAX_QUERIES_TO_ANALYZE < 0:
        errors.append("MAX_QUERIES_TO_ANALYZE must be >= 0")

    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False

    return True
