from app.core.time_utils import ensure_aware, utcnow
from app.schemas.auth import UserOut


def serialize_user(user: dict) -> UserOut:
    return UserOut(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        avatar_emoji=user.get("avatar_emoji", "🌸"),
        trial_started_at=user["trial_started_at"],
        trial_ends_at=user["trial_ends_at"],
        subscription_status=subscription_status(user),
        subscription_tier=user.get("subscription_tier"),
        subscription_expires_at=user.get("subscription_expires_at"),
    )


def subscription_status(user: dict) -> str:
    """Any real subscription-lifecycle status (active, free, canceled,
    expired, billing_issue — whatever RevenueCat sync writes) is trusted
    as-is. Only "trialing" or an unset status falls back to a fresh
    trial-date computation, since "trialing" is the one status that can go
    stale on its own without any subscription event ever firing."""
    stored_status = user.get("subscription_status")
    if stored_status and stored_status != "trialing":
        return stored_status
    trial_ends_at = ensure_aware(user["trial_ends_at"])
    if utcnow() < trial_ends_at:
        return "trialing"
    return "expired"
