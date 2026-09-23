from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

from app.core.config import get_settings
from app.core.db import get_db
from app.services import revenuecat

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/revenuecat", status_code=status.HTTP_200_OK)
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """RevenueCat calls this on every purchase/renewal/cancellation/
    expiration/billing-issue event. Authenticated via a shared secret you
    set as the Authorization header value in the RevenueCat dashboard's
    webhook settings (Project Settings -> Webhooks) — not a JWT, since
    RevenueCat isn't one of our users.

    Every event is logged to `billing_events` for audit/support regardless
    of whether processing succeeds, then triggers a fresh subscriber fetch
    (see app/services/revenuecat.py) rather than trusting the event
    payload's own status fields."""
    settings = get_settings()
    if not settings.revenuecat_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook not configured")
    if authorization != settings.revenuecat_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook credentials")

    payload = await request.json()
    event = payload.get("event", {})
    app_user_id = event.get("app_user_id")
    if not app_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event.app_user_id")

    await db.billing_events.insert_one(
        {
            "user_id": app_user_id,
            "event_type": event.get("type"),
            "environment": event.get("environment"),
            "raw_event": event,
            "received_at": datetime.now(timezone.utc),
        }
    )

    try:
        await revenuecat.sync_entitlement(db, app_user_id)
    except ValueError:
        # app_user_id isn't one of our real user ids (e.g. a RevenueCat test
        # event, or a purchase made before Purchases.logIn ran) — already
        # logged above for follow-up, nothing to sync against.
        pass
    except revenuecat.RevenueCatUnavailable:
        # Webhook secret was configured but the secret API key wasn't —
        # logged above; the event is durably recorded and can be replayed
        # once the key is set.
        pass

    return {"received": True}
