import pytest

from app.core.config import get_settings
from app.services import email


@pytest.mark.asyncio
async def test_send_email_returns_false_when_unconfigured(monkeypatch):
    monkeypatch.setattr(get_settings(), "resend_api_key", None)
    sent = await email.send_email(to="a@example.com", subject="Hi", html="<p>hi</p>", text="hi")
    assert sent is False


@pytest.mark.asyncio
async def test_send_email_posts_to_resend_when_configured(monkeypatch):
    monkeypatch.setattr(get_settings(), "resend_api_key", "test-key")
    monkeypatch.setattr(get_settings(), "resend_from_email", "Soft Life Society <test@resend.dev>")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(email.httpx, "AsyncClient", FakeAsyncClient)

    sent = await email.send_email(to="a@example.com", subject="Hi", html="<p>hi</p>", text="hi")
    assert sent is True
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["json"]["to"] == ["a@example.com"]
    assert captured["json"]["from"] == "Soft Life Society <test@resend.dev>"
    assert captured["json"]["subject"] == "Hi"


@pytest.mark.asyncio
async def test_send_email_returns_false_on_http_error(monkeypatch):
    import httpx

    monkeypatch.setattr(get_settings(), "resend_api_key", "test-key")

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.ConnectError("boom")

    monkeypatch.setattr(email.httpx, "AsyncClient", FailingAsyncClient)

    sent = await email.send_email(to="a@example.com", subject="Hi", html="<p>hi</p>", text="hi")
    assert sent is False


def test_password_reset_email_includes_url_and_expiry_note():
    html, text = email.password_reset_email("softlifesociety://reset-password?token=abc123")
    assert "softlifesociety://reset-password?token=abc123" in html
    assert "softlifesociety://reset-password?token=abc123" in text
    assert "30 minutes" in html
    assert "30 minutes" in text


@pytest.mark.asyncio
async def test_send_password_reset_email_uses_reset_subject(monkeypatch):
    captured = {}

    async def fake_send_email(*, to, subject, html, text):
        captured.update(to=to, subject=subject, html=html, text=text)
        return True

    monkeypatch.setattr(email, "send_email", fake_send_email)

    sent = await email.send_password_reset_email(to="a@example.com", reset_url="softlifesociety://reset-password?token=xyz")
    assert sent is True
    assert captured["to"] == "a@example.com"
    assert "Reset your Soft Life Society password" == captured["subject"]
    assert "xyz" in captured["html"]


@pytest.mark.asyncio
async def test_password_reset_request_falls_back_to_log_when_resend_unconfigured(client, test_db, caplog):
    monkeypatch_target = get_settings()
    assert monkeypatch_target.resend_api_key is None  # dev default

    signup = await client.post(
        "/auth/signup", json={"name": "Reset Test", "email": "resendfallback@example.com", "password": "supersecret1"}
    )
    assert signup.status_code == 201

    import logging

    with caplog.at_level(logging.INFO, logger="soft_life_society"):
        response = await client.post("/auth/password-reset/request", json={"email": "resendfallback@example.com"})
    assert response.status_code == 200
    assert any("Password reset requested for resendfallback@example.com" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_password_reset_request_sends_real_email_when_resend_configured(client, test_db, monkeypatch):
    monkeypatch.setattr(get_settings(), "resend_api_key", "test-key")

    captured = {}

    async def fake_send_password_reset_email(*, to, reset_url):
        captured["to"] = to
        captured["reset_url"] = reset_url
        return True

    import app.routers.auth as auth_router

    monkeypatch.setattr(auth_router, "send_password_reset_email", fake_send_password_reset_email)

    signup = await client.post(
        "/auth/signup", json={"name": "Reset Test", "email": "resendreal@example.com", "password": "supersecret1"}
    )
    assert signup.status_code == 201

    response = await client.post("/auth/password-reset/request", json={"email": "resendreal@example.com"})
    assert response.status_code == 200
    assert captured["to"] == "resendreal@example.com"
    assert captured["reset_url"].startswith("softlifesociety://reset-password?token=")
