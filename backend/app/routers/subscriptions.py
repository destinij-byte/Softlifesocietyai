from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.auth import UserOut
from app.services import revenuecat
from app.services.users import serialize_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Display-only catalog for the paywall UI. The actual product IDs/prices
# that matter are configured in App Store Connect / Play Console / RevenueCat
# — these labels must be kept in sync with whatever you set up there, but
# this dict itself grants nothing (see /sync and app/routers/webhooks.py for
# the only two places subscription state is ever actually written).
TIERS = {
    "free": {"label": "Free", "price_usd": 0.0, "billing_period": None, "emoji": "🤍"},
    "monthly": {"label": "Monthly", "price_usd": 19.99, "billing_period": "month", "emoji": "🌙"},
    "annual": {"label": "Annual", "price_usd": 119.99, "billing_period": "year", "emoji": "✨"},
    "founding": {"label": "Founding Member — Annual", "price_usd": 79.99, "billing_period": "year", "emoji": "👑"},
}


@router.get("/tiers")
async def get_tiers():
    return TIERS


@router.get("/status", response_model=UserOut)
async def get_status(current_user: dict = Depends(get_current_user)):
    return serialize_user(current_user)


@router.post("/sync", response_model=UserOut)
async def sync_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Call this immediately after a client-side purchase (Purchases.purchasePackage)
    completes, so entitlement reflects reality without waiting for the
    webhook. Never trusts anything the client claims about which tier was
    bought — always re-fetches from RevenueCat server-to-server."""
    try:
        await revenuecat.sync_entitlement(db, str(current_user["_id"]))
    except revenuecat.RevenueCatUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscription verification isn't configured yet.",
        )
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return serialize_user(updated)
