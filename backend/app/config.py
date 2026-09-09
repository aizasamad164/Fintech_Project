"""
Central app configuration.
Loads all secrets from environment variables (.env) — NEVER hardcode keys here.
Satisfies NFR-2.1: no third-party API keys exposed to client bundles.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    jwt_secret_key: str

    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str

    # Market data (FR-2.1)
    finnhub_api_key: str = ""
    polygon_api_key: str = ""

    # LLM (FR-5.2)
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"

    # Cache / rate limiting (FR-2.4)
    market_data_cache_ttl_seconds: int = 300
    max_requests_per_minute: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
