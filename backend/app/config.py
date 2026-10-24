"""
Central app configuration.
Loads all secrets from environment variables (.env) — NEVER hardcode keys here.
Satisfies NFR-2.1: no third-party API keys exposed to client bundles.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always read backend/.env, no matter which folder uvicorn is started from
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_env: str = "development"
    jwt_secret_key: str = "super-secret-jwt-key"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""

    # Market data (FR-2.1)
    finnhub_api_key: str = ""
    polygon_api_key: str = ""

    # LLM (FR-5.2)
    groq_api_key: str = ""
    # Agent model (needs tool calling). Llama 3.x on Groq moved to enterprise-only
    # plans, so default to OpenAI's open-weight GPT-OSS models. Override in .env;
    # run `python check_models.py` to see what your key can use.
    groq_model: str = "openai/gpt-oss-120b"
    # Smaller, faster model for the 3-bullet dashboard explanation
    groq_explain_model: str = "openai/gpt-oss-20b"

    # CORS: comma-separated frontend origins
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Cache / rate limiting (FR-2.4)
    market_data_cache_ttl_seconds: int = 300
    max_requests_per_minute: int = 60

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

    # Uppercase aliases for backward-compatibility across modules
    @property
    def GROQ_API_KEY(self) -> str:
        return self.groq_api_key

    @property
    def GROQ_MODEL(self) -> str:
        return self.groq_model


settings = Settings()

# 1. Import SECTOR_CONFIGS directly from unmodified ml_config.py
from app.ml_config import SECTOR_CONFIGS

# 2. Define GENERAL_MODEL_CONFIG locally so ml_config.py doesn't need edits
GENERAL_MODEL_CONFIG = {
    "model_file": "general_ensemble_model.joblib",
    "scaler_file": "general_scaler.joblib",
    "benchmark_ticker": "SPY",
}