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

    # RevenueCat — real subscription entitlement verification. The secret key
    # is a server-to-server credential (never shipped to the client) used to
    # ask "what is this user actually entitled to right now" instead of
    # trusting anything the client claims. The webhook secret is whatever
    # value you configure as the Authorization header in the RevenueCat
    # dashboard's webhook settings — we just compare it verbatim. Both are
    # None until you create a RevenueCat account and set them; subscription
    # sync/webhook endpoints fail closed (never silently grant access) until
    # they're configured.
    revenuecat_secret_api_key: str | None = None
    revenuecat_webhook_secret: str | None = None

    # Resend — transactional email (password reset). None until you create a
    # Resend account; password-reset requests fail over to logging the token
    # server-side (dev-mode behavior) rather than silently pretending to send.
    resend_api_key: str | None = None
    resend_from_email: str = "Soft Life Society <onboarding@resend.dev>"

    # Base URL the password-reset email's link is built from — the app's own
    # custom URL scheme (see frontend/app.json "scheme") by default, so
    # tapping the link on a device with the app installed opens it straight
    # to the reset screen. Override with a universal-link https:// URL once
    # one is set up, without changing any other reset-flow code.
    password_reset_url_base: str = "softlifesociety://reset-password"

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
    if not settings.revenuecat_secret_api_key or not settings.revenuecat_webhook_secret:
        logger.warning(
            "RevenueCat is not fully configured (REVENUECAT_SECRET_API_KEY / REVENUECAT_WEBHOOK_SECRET) — "
            "subscription sync and the RevenueCat webhook will refuse to grant entitlement until both are set."
        )
    if not settings.resend_api_key:
        logger.warning(
            "RESEND_API_KEY is not set in production — password reset emails will not be delivered; "
            "the reset token will only be logged server-side."
        )
