from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.auth import UserOut
from app.services.users import serialize_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

TIERS = {
    "free": {"label": "Free", "price_usd": 0.0, "emoji": "🤍"},
    "monthly": {"label": "Monthly", "price_usd": 14.99, "emoji": "🌙"},
    "annual": {"label": "Annual", "price_usd": 99.0, "emoji": "✨"},
}


class SubscribeRequest(BaseModel):
    tier: str


@router.get("/tiers")
async def get_tiers():
    return TIERS


@router.get("/status", response_model=UserOut)
async def get_status(current_user: dict = Depends(get_current_user)):
    return serialize_user(current_user)


@router.post("/subscribe", response_model=UserOut)
async def subscribe(
    payload: SubscribeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if payload.tier not in TIERS:
        raise HTTPException(status_code=400, detail="Unknown subscription tier")

    status = "free" if payload.tier == "free" else "active"
    tier = None if payload.tier == "free" else payload.tier
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"subscription_status": status, "subscription_tier": tier}},
    )
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return serialize_user(updated)


@router.post("/cancel", response_model=UserOut)
async def cancel(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"subscription_status": "canceled", "subscription_tier": None}},
    )
    updated = await db.users.find_one({"_id": current_user["_id"]})
    return serialize_user(updated)
