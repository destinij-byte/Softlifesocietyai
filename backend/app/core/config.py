import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("soft_life_society")


_DEFAULT_MONGODB_URI = "mongodb://localhost:27017"
_DEFAULT_ALLOWED_ORIGINS = "http://localhost:8081,http://localhost:19006,exp://localhost:19000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    mongodb_uri: str = _DEFAULT_MONGODB_URI
    mongodb_db_name: str = "softlifesociety"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    trial_length_days: int = 7

    anthropic_api_key: str | None = None
    luna_model: str = "claude-opus-5"

    # Comma-separated list of allowed CORS origins, e.g. "https://app.example.com,exp://localhost:19000"
    allowed_origins: str = _DEFAULT_ALLOWED_ORIGINS

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_production_settings(settings: Settings) -> None:
    """Fail fast on startup rather than silently running production traffic on an
    insecure default. Called from the FastAPI startup event, not at import time,
    so tests and local dev never pay for it unless ENVIRONMENT=production.

    Hard-fails on misconfiguration that would be actively wrong in production
    (a dev secret, a dev database, a dev-only CORS list); only warns on a
    missing Anthropic key since the app is designed to degrade gracefully to
    templated Luna/local meal suggestions — a deliberate product choice, not
    a bug — but it's loud in the logs so it's never silently unnoticed."""
    if not settings.is_production:
        return
    if settings.jwt_secret == "change-me-in-production":
        raise RuntimeError(
            "JWT_SECRET is still the insecure default. Set a strong, unique JWT_SECRET "
            "before running with ENVIRONMENT=production."
        )
    if len(settings.jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters in production.")
    if settings.mongodb_uri == _DEFAULT_MONGODB_URI:
        raise RuntimeError(
            "MONGODB_URI is still the local-dev default (mongodb://localhost:27017). "
            "Set it to your production MongoDB connection string before running with ENVIRONMENT=production."
        )
    if settings.allowed_origins == _DEFAULT_ALLOWED_ORIGINS:
        raise RuntimeError(
            "ALLOWED_ORIGINS is still the local-dev default — the production app can't reach "
            "an API that only allows localhost/exp:// origins. Set ALLOWED_ORIGINS to your real "
            "production origin(s) before running with ENVIRONMENT=production."
        )
    if not settings.anthropic_api_key:
        logger.warning(
            "ANTHROPIC_API_KEY is not set in production — Luna and Nourish AI will run in their "
            "offline/templated fallback mode for every user until this is configured."
        )
