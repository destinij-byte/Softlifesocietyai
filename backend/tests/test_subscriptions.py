from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.core.config import get_settings
from app.services import revenuecat


def _future_iso(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _past_iso(days: int = 5) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- entitlement_from_subscriber (pure function, no network) ---


def test_entitlement_from_subscriber_no_record_is_free():
    status, tier, expires_at = revenuecat.entitlement_from_subscriber(None)
    assert status == "free"
    assert tier is None
    assert expires_at is None


def test_entitlement_from_subscriber_active_entitlement_maps_tier():
    payload = {
        "subscriber": {
            "entitlements": {
                "premium_annual": {"expires_date": _future_iso(300)},
            }
        }
    }
    status, tier, expires_at = revenuecat.entitlement_from_subscriber(payload)
    assert status == "active"
    assert tier == "annual"
    assert expires_at is not None


def test_entitlement_from_subscriber_expired_entitlement_is_free():
    payload = {
        "subscriber": {
            "entitlements": {
                "premium_monthly": {"expires_date": _past_iso(5)},
            }
        }
    }
    status, tier, expires_at = revenuecat.entitlement_from_subscriber(payload)
    assert status == "free"
    assert tier is None
    assert expires_at is None


def test_entitlement_from_subscriber_non_expiring_entitlement_is_active():
    payload = {
        "subscriber": {
            "entitlements": {
                "premium_founding": {"expires_date": None},
            }
        }
    }
    status, tier, expires_at = revenuecat.entitlement_from_subscriber(payload)
    assert status == "active"
    assert tier == "founding"
    assert expires_at is None


def test_entitlement_from_subscriber_unmapped_entitlement_id_passed_through():
    payload = {
        "subscriber": {
            "entitlements": {
                "some_new_entitlement": {"expires_date": _future_iso(10)},
            }
        }
    }
    status, tier, _ = revenuecat.entitlement_from_subscriber(payload)
    assert status == "active"
    assert tier == "some_new_entitlement"


# --- fetch_subscriber / sync_entitlement fail closed when unconfigured ---


@pytest.mark.asyncio
async def test_fetch_subscriber_raises_when_unconfigured(monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", None)
    with pytest.raises(revenuecat.RevenueCatUnavailable):
        await revenuecat.fetch_subscriber("some-user-id")


@pytest.mark.asyncio
async def test_sync_entitlement_raises_when_unconfigured(test_db, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", None)
    with pytest.raises(revenuecat.RevenueCatUnavailable):
        await revenuecat.sync_entitlement(test_db, "507f1f77bcf86cd799439011")


@pytest.mark.asyncio
async def test_sync_entitlement_rejects_invalid_user_id(test_db, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", "test-key")
    with pytest.raises(ValueError):
        await revenuecat.sync_entitlement(test_db, "not-an-object-id")


@pytest.mark.asyncio
async def test_sync_entitlement_writes_active_tier_from_mocked_api(test_db, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", "test-key")

    async def fake_fetch_subscriber(app_user_id: str):
        return {
            "subscriber": {
                "entitlements": {
                    "premium_monthly": {"expires_date": _future_iso(30)},
                }
            }
        }

    monkeypatch.setattr(revenuecat, "fetch_subscriber", fake_fetch_subscriber)

    user = await test_db.users.find_one({})
    if user is None:
        result = await test_db.users.insert_one(
            {"email": "sub-test@example.com", "name": "Sub Test", "password_hash": "x", "subscription_status": "free"}
        )
        user_id = str(result.inserted_id)
    else:
        user_id = str(user["_id"])

    update = await revenuecat.sync_entitlement(test_db, user_id)
    assert update["subscription_status"] == "active"
    assert update["subscription_tier"] == "monthly"

    from bson import ObjectId

    stored = await test_db.users.find_one({"_id": ObjectId(user_id)})
    assert stored["subscription_status"] == "active"
    assert stored["subscription_tier"] == "monthly"


# --- GET /subscriptions/tiers ---


@pytest.mark.asyncio
async def test_get_tiers_returns_pricing_catalog(client):
    response = await client.get("/subscriptions/tiers")
    assert response.status_code == 200
    body = response.json()
    assert body["monthly"]["price_usd"] == 19.99
    assert body["annual"]["price_usd"] == 119.99
    assert body["founding"]["price_usd"] == 79.99


# --- old fake-activation endpoints must be gone ---


@pytest.mark.asyncio
async def test_subscribe_endpoint_no_longer_exists(client, auth_headers):
    headers = await auth_headers()
    response = await client.post("/subscriptions/subscribe", json={"tier": "monthly"}, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_endpoint_no_longer_exists(client, auth_headers):
    headers = await auth_headers()
    response = await client.post("/subscriptions/cancel", headers=headers)
    assert response.status_code == 404


# --- POST /subscriptions/sync ---


@pytest.mark.asyncio
async def test_sync_requires_auth(client):
    response = await client.post("/subscriptions/sync")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sync_returns_503_when_revenuecat_unconfigured(client, auth_headers, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", None)
    headers = await auth_headers()
    response = await client.post("/subscriptions/sync", headers=headers)
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_sync_never_trusts_client_tier_claim(client, auth_headers, monkeypatch):
    """A user cannot grant themselves a paid tier by POSTing a tier in the body —
    /sync takes no body at all, and entitlement always comes from the mocked
    RevenueCat fetch, not anything the client sent."""
    headers = await auth_headers()
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", "test-key")

    async def fake_fetch_subscriber(app_user_id: str):
        return None  # RevenueCat has no record -> free, regardless of client intent

    monkeypatch.setattr(revenuecat, "fetch_subscriber", fake_fetch_subscriber)

    response = await client.post(
        "/subscriptions/sync",
        json={"tier": "founding", "subscription_status": "active"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["subscription_status"] in ("free", "trialing")
    assert body.get("subscription_tier") in (None, "free")


@pytest.mark.asyncio
async def test_sync_grants_active_tier_from_verified_revenuecat_response(client, auth_headers, monkeypatch):
    headers = await auth_headers()
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", "test-key")

    async def fake_fetch_subscriber(app_user_id: str):
        return {
            "subscriber": {
                "entitlements": {
                    "premium_annual": {"expires_date": _future_iso(300)},
                }
            }
        }

    monkeypatch.setattr(revenuecat, "fetch_subscriber", fake_fetch_subscriber)

    response = await client.post("/subscriptions/sync", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["subscription_status"] == "active"
    assert body["subscription_tier"] == "annual"


# --- POST /webhooks/revenuecat ---


@pytest.mark.asyncio
async def test_webhook_returns_503_when_secret_unconfigured(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_secret", None)
    response = await client.post(
        "/webhooks/revenuecat",
        json={"event": {"app_user_id": "abc", "type": "INITIAL_PURCHASE"}},
        headers={"Authorization": "whatever"},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_webhook_rejects_wrong_secret(monkeypatch, client):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_secret", "correct-secret")
    response = await client.post(
        "/webhooks/revenuecat",
        json={"event": {"app_user_id": "abc", "type": "INITIAL_PURCHASE"}},
        headers={"Authorization": "wrong-secret"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_rejects_missing_app_user_id(monkeypatch, client):
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_secret", "correct-secret")
    response = await client.post(
        "/webhooks/revenuecat",
        json={"event": {"type": "INITIAL_PURCHASE"}},
        headers={"Authorization": "correct-secret"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_logs_event_and_syncs_entitlement(client, auth_headers, test_db, monkeypatch):
    headers = await auth_headers()
    me = await client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    monkeypatch.setattr(get_settings(), "revenuecat_webhook_secret", "correct-secret")
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", "test-key")

    async def fake_fetch_subscriber(app_user_id: str):
        return {
            "subscriber": {
                "entitlements": {
                    "premium_monthly": {"expires_date": _future_iso(30)},
                }
            }
        }

    monkeypatch.setattr(revenuecat, "fetch_subscriber", fake_fetch_subscriber)

    response = await client.post(
        "/webhooks/revenuecat",
        json={"event": {"app_user_id": user_id, "type": "INITIAL_PURCHASE", "environment": "SANDBOX"}},
        headers={"Authorization": "correct-secret"},
    )
    assert response.status_code == 200
    assert response.json() == {"received": True}

    logged = await test_db.billing_events.find_one({"user_id": user_id})
    assert logged is not None
    assert logged["event_type"] == "INITIAL_PURCHASE"

    me_after = await client.get("/auth/me", headers=headers)
    assert me_after.json()["subscription_status"] == "active"
    assert me_after.json()["subscription_tier"] == "monthly"


@pytest.mark.asyncio
async def test_webhook_tolerates_unknown_app_user_id(client, monkeypatch, test_db):
    """A RevenueCat test event or a purchase made before Purchases.logIn ran
    uses an app_user_id that isn't a real Mongo ObjectId — must not 500."""
    monkeypatch.setattr(get_settings(), "revenuecat_webhook_secret", "correct-secret")

    response = await client.post(
        "/webhooks/revenuecat",
        json={"event": {"app_user_id": "$RCAnonymousID:abc123", "type": "TEST"}},
        headers={"Authorization": "correct-secret"},
    )
    assert response.status_code == 200
    logged = await test_db.billing_events.find_one({"user_id": "$RCAnonymousID:abc123"})
    assert logged is not None


@pytest.mark.asyncio
async def test_webhook_event_recorded_even_when_revenuecat_unavailable(client, monkeypatch, test_db, auth_headers):
    headers = await auth_headers()
    me = await client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    monkeypatch.setattr(get_settings(), "revenuecat_webhook_secret", "correct-secret")
    monkeypatch.setattr(get_settings(), "revenuecat_secret_api_key", None)

    response = await client.post(
        "/webhooks/revenuecat",
        json={"event": {"app_user_id": user_id, "type": "RENEWAL"}},
        headers={"Authorization": "correct-secret"},
    )
    assert response.status_code == 200
    logged = await test_db.billing_events.find_one({"user_id": user_id})
    assert logged is not None
