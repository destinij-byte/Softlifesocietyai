from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "softlifesociety"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    trial_length_days: int = 7

    anthropic_api_key: str | None = None
    luna_model: str = "claude-opus-5"

    # Comma-separated list of allowed CORS origins, e.g. "https://app.example.com,exp://localhost:19000"
    allowed_origins: str = "http://localhost:8081,http://localhost:19006,exp://localhost:19000"

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
    so tests and local dev never pay for it unless ENVIRONMENT=production."""
    if not settings.is_production:
        return
    if settings.jwt_secret == "change-me-in-production":
        raise RuntimeError(
            "JWT_SECRET is still the insecure default. Set a strong, unique JWT_SECRET "
            "before running with ENVIRONMENT=production."
        )
    if len(settings.jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters in production.")
