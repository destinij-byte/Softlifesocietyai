from datetime import datetime, timezone

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
    )


def subscription_status(user: dict) -> str:
    stored_status = user.get("subscription_status")
    if stored_status in ("active", "free"):
        return stored_status
    trial_ends_at = user["trial_ends_at"]
    if trial_ends_at.tzinfo is None:
        trial_ends_at = trial_ends_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) < trial_ends_at:
        return "trialing"
    return "expired"
