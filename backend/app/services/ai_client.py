import anthropic

from app.core.config import get_settings

_client: anthropic.AsyncAnthropic | None = None


def get_ai_client() -> anthropic.AsyncAnthropic | None:
    global _client
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client
