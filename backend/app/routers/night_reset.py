from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.night_reset import NightCheckinIn, NightCheckinOut
from app.services.day_summary import get_day_summary

router = APIRouter(prefix="/night-reset", tags=["night-reset"])


@router.get("/today", response_model=NightCheckinOut)
async def get_today_checkin(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    doc = await db.daily_checkins.find_one({"user_id": str(current_user["_id"]), "log_date": today})
    summary = await get_day_summary(db, current_user, today)
    return NightCheckinOut(
        log_date=today,
        win=doc.get("win", "") if doc else "",
        gratitude=doc.get("gratitude", "") if doc else "",
        tomorrow_focus=doc.get("tomorrow_focus", "") if doc else "",
        completed=doc is not None,
        day_summary=summary,
    )


@router.post("/today", response_model=NightCheckinOut)
async def submit_today_checkin(
    payload: NightCheckinIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Upsert-per-day, same pattern as /home/mood — a missed night is simply
    absent, never flagged, and resubmitting the same day just overwrites."""
    today = date.today().isoformat()
    user_id = str(current_user["_id"])
    now = datetime.now(timezone.utc)
    fields = {
        "win": payload.win.strip(),
        "gratitude": payload.gratitude.strip(),
        "tomorrow_focus": payload.tomorrow_focus.strip(),
    }
    await db.daily_checkins.update_one(
        {"user_id": user_id, "log_date": today},
        {"$set": {**fields, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    summary = await get_day_summary(db, current_user, today)
    return NightCheckinOut(log_date=today, completed=True, day_summary=summary, **fields)
