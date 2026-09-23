from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.time_utils import ensure_aware, utcnow

DEFAULT_MESSAGE = "You've made too many requests — please try again shortly."


async def check_rate_limit(db: AsyncIOMotorDatabase, key: str, limit: int, window: timedelta, message: str) -> None:
    """Shared sliding-window limiter (one doc per key in `rate_limits`) — the
    same pattern Luna's chat limiter used, generalized so every endpoint that
    needs one (signup, password reset, AI-cost endpoints) shares one
    collection and one code path instead of each reinventing it."""
    window_start = utcnow() - window
    record = await db.rate_limits.find_one({"key": key})
    if record and ensure_aware(record.get("window_start", utcnow())) > window_start:
        if record.get("count", 0) >= limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
        await db.rate_limits.update_one({"key": key}, {"$inc": {"count": 1}})
    else:
        await db.rate_limits.update_one({"key": key}, {"$set": {"window_start": utcnow(), "count": 1}}, upsert=True)


def client_ip(request: Request) -> str:
    # Behind a proxy/load balancer, the real client is the first hop in
    # X-Forwarded-For — trust it if present, otherwise fall back to the
    # direct connection (true in local dev and any non-proxied deploy).
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_by_ip(bucket: str, limit: int, window: timedelta, message: str = DEFAULT_MESSAGE):
    """A FastAPI dependency limiting unauthenticated endpoints (signup,
    password-reset-request) by client IP, since there's no user yet to key on."""

    async def _dep(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)) -> None:
        await check_rate_limit(db, f"{bucket}:{client_ip(request)}", limit, window, message)

    return _dep


def rate_limit_by_user(bucket: str, limit: int, window: timedelta, message: str = DEFAULT_MESSAGE):
    """A FastAPI dependency limiting authenticated, AI-cost endpoints by
    user id. Reuses get_current_user, which FastAPI caches per-request, so
    this doesn't add a second auth lookup on top of the endpoint's own."""

    async def _dep(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)) -> None:
        await check_rate_limit(db, f"{bucket}:{current_user['_id']}", limit, window, message)

    return _dep
