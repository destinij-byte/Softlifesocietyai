from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "softlifesociety"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    trial_length_days: int = 7

    anthropic_api_key: str | None = None
    luna_model: str = "claude-opus-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
