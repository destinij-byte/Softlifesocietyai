"""Server-to-server RevenueCat integration — the piece that makes
subscription state real instead of trust-the-client.

UNTESTED AGAINST A LIVE REVENUECAT ACCOUNT. This follows RevenueCat's
documented REST API (GET /v1/subscribers/{app_user_id}) and webhook event
shape, but has only been exercised against mocked payloads in
tests/test_subscriptions.py — there is no RevenueCat account configured in
this environment to verify against. Before this goes live: create a
RevenueCat project, configure REVENUECAT_SECRET_API_KEY and
REVENUECAT_WEBHOOK_SECRET, create real products/entitlements in App Store
Connect / Play Console, and confirm ENTITLEMENT_TIER_MAP below matches the
entitlement identifiers you actually configure in the RevenueCat dashboard.

Design: RevenueCat is always the source of truth. Rather than hand-parsing
webhook event *types* (INITIAL_PURCHASE, RENEWAL, CANCELLATION,
EXPIRATION, BILLING_ISSUE, ...) into our own state machine — which would
mean re-implementing RevenueCat's own grace-period and billing-retry
logic — every sync (webhook-triggered or client-triggered) re-fetches the
subscriber's current entitlements from RevenueCat's API and mirrors
exactly that into our `users` collection. The webhook is just a "go check
now" signal, not a payload we trust for exact state.
"""

from datetime import datetime, timezone

import httpx
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings

REVENUECAT_API_BASE = "https://api.revenuecat.com/v1"

# Maps a RevenueCat *entitlement identifier* (configured in the RevenueCat
# dashboard, not a raw store product ID) to our internal subscription_tier.
# Update this to match whatever entitlement identifiers you actually create.
ENTITLEMENT_TIER_MAP = {
    "premium_monthly": "monthly",
    "premium_annual": "annual",
    "premium_founding": "founding",
}


class RevenueCatUnavailable(Exception):
    """Raised when a sync is attempted but no RevenueCat secret key is
    configured — callers should treat this as "cannot verify," never as
    "grant access anyway."""


async def fetch_subscriber(app_user_id: str) -> dict | None:
    """GET /v1/subscribers/{app_user_id}. Returns None if RevenueCat has no
    record of this user (never purchased anything)."""
    settings = get_settings()
    if not settings.revenuecat_secret_api_key:
        raise RevenueCatUnavailable("REVENUECAT_SECRET_API_KEY is not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{REVENUECAT_API_BASE}/subscribers/{app_user_id}",
            headers={"Authorization": f"Bearer {settings.revenuecat_secret_api_key}"},
        )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def entitlement_from_subscriber(payload: dict | None) -> tuple[str, str | None, datetime | None]:
    """(subscription_status, subscription_tier, subscription_expires_at)
    from a RevenueCat subscriber payload's active entitlements. `payload`
    is None when RevenueCat has no record of the user at all."""
    if payload is None:
        return "free", None, None

    entitlements = payload.get("subscriber", {}).get("entitlements", {})
    now = datetime.now(timezone.utc)

    for key, info in entitlements.items():
        expires_str = info.get("expires_date")
        if expires_str is None:
            # No expiration = a non-expiring (e.g. lifetime/promotional) entitlement.
            return "active", ENTITLEMENT_TIER_MAP.get(key, key), None
        expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
        if expires_at > now:
            return "active", ENTITLEMENT_TIER_MAP.get(key, key), expires_at

    return "free", None, None


async def sync_entitlement(db: AsyncIOMotorDatabase, user_id: str) -> dict:
    """Fetch ground truth from RevenueCat and write it to the user doc.
    Returns the fields written. Raises RevenueCatUnavailable if not
    configured — callers must not fall back to trusting the client."""
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        raise ValueError(f"Not a valid user id: {user_id!r}")

    subscriber = await fetch_subscriber(user_id)
    status, tier, expires_at = entitlement_from_subscriber(subscriber)

    update = {
        "subscription_status": status,
        "subscription_tier": tier,
        "subscription_expires_at": expires_at,
    }
    await db.users.update_one({"_id": object_id}, {"$set": update})
    return update
