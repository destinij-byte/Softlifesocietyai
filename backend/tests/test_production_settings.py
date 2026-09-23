"""2.0 Phase A: validate_production_settings should fail fast on every
dev-default that would actively break or endanger a production deploy, and
only warn (not fail) on a missing Anthropic key since offline/templated
fallback is a deliberate, graceful degradation."""

import pytest

from app.core.config import Settings, validate_production_settings


def _settings(**overrides) -> Settings:
    base = {
        "environment": "production",
        "jwt_secret": "x" * 40,
        "mongodb_uri": "mongodb+srv://prod-cluster.example.net/db",
        "allowed_origins": "https://app.softlifesociety.example",
        "anthropic_api_key": "sk-ant-real-key",
    }
    base.update(overrides)
    return Settings(**base)


def test_fully_configured_production_settings_pass():
    validate_production_settings(_settings())  # should not raise


def test_dev_default_jwt_secret_fails():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_settings(_settings(jwt_secret="change-me-in-production"))


def test_short_jwt_secret_fails():
    with pytest.raises(RuntimeError, match="32 characters"):
        validate_production_settings(_settings(jwt_secret="short"))


def test_dev_default_mongodb_uri_fails():
    with pytest.raises(RuntimeError, match="MONGODB_URI"):
        validate_production_settings(_settings(mongodb_uri="mongodb://localhost:27017"))


def test_dev_default_cors_origins_fails():
    with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
        validate_production_settings(
            _settings(allowed_origins="http://localhost:8081,http://localhost:19006,exp://localhost:19000")
        )


def test_missing_anthropic_key_warns_but_does_not_raise(caplog):
    validate_production_settings(_settings(anthropic_api_key=None))  # should not raise
    assert any("ANTHROPIC_API_KEY" in record.message for record in caplog.records)


def test_non_production_environment_skips_all_checks():
    dev_settings = Settings(environment="development", jwt_secret="change-me-in-production")
    validate_production_settings(dev_settings)  # should not raise
