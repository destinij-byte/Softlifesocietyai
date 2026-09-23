"""Transactional email via Resend (resend.com) — currently only used for
password-reset links.

Fails soft, not closed: unlike RevenueCat's entitlement sync, a missing
provider or a delivery failure here is never a security boundary — it's a
UX gap. If RESEND_API_KEY isn't configured, or Resend's API call fails,
`send_password_reset_email` returns False and the caller falls back to the
pre-existing dev-mode behavior (log the reset token server-side) rather
than blocking account recovery.
"""
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger("soft_life_society")

RESEND_API_BASE = "https://api.resend.com"


async def send_email(*, to: str, subject: str, html: str, text: str) -> bool:
    """True if Resend accepted the email for delivery, False otherwise
    (including when no API key is configured). Never raises — a broken
    email provider must not turn into a 500 for the caller."""
    settings = get_settings()
    if not settings.resend_api_key:
        return False

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{RESEND_API_BASE}/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": settings.resend_from_email, "to": [to], "subject": subject, "html": html, "text": text},
            )
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Resend email delivery failed for %s", to)
        return False


def password_reset_email(reset_url: str) -> tuple[str, str]:
    """(html, text) bodies for a password-reset email."""
    html = f"""
    <div style="font-family: -apple-system, Helvetica, Arial, sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color:#1a1a1a;">Reset your Soft Life Society password</h2>
      <p style="color:#4a4a4a;">Tap the button below to choose a new password. This link expires in 30 minutes.</p>
      <p style="margin: 24px 0;">
        <a href="{reset_url}" style="background:#1a1a1a;color:#D4AF37;padding:14px 28px;border-radius:24px;text-decoration:none;font-weight:600;display:inline-block;">
          Reset password
        </a>
      </p>
      <p style="color:#8a8a8a;font-size:13px;">If you didn't request this, you can safely ignore this email.</p>
    </div>
    """
    text = f"Reset your Soft Life Society password: {reset_url}\n\nThis link expires in 30 minutes. If you didn't request this, you can safely ignore this email."
    return html, text


async def send_password_reset_email(*, to: str, reset_url: str) -> bool:
    html, text = password_reset_email(reset_url)
    return await send_email(to=to, subject="Reset your Soft Life Society password", html=html, text=text)
