from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.pillars import PILLARS
from app.services.blueprint_context import get_blueprint_context

router = APIRouter(prefix="/home", tags=["home"])

MOODS = {
    "tired": {"label": "Tired", "emoji": "😮‍💨"},
    "tender": {"label": "Tender", "emoji": "🥺"},
    "good": {"label": "Good", "emoji": "🙂"},
    "calm": {"label": "Calm", "emoji": "😌"},
    "radiant": {"label": "Radiant", "emoji": "✨"},
}


class MoodIn(BaseModel):
    mood: str


class MoodOut(BaseModel):
    mood: str | None
    log_date: str


class PillarOut(BaseModel):
    pillar: str
    label: str
    emoji: str


class HomeContextOut(BaseModel):
    era: str | None
    era_label: str | None
    becoming: str
    top_pillars: list[PillarOut]


@router.get("/context", response_model=HomeContextOut)
async def get_home_context(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """What Home reads to stay era-aware — an era banner and a priority order
    for its tiles — without Home querying the Blueprint collection itself."""
    ctx = await get_blueprint_context(db, str(current_user["_id"]))
    return HomeContextOut(
        era=ctx.era,
        era_label=ctx.era_label,
        becoming=ctx.becoming,
        top_pillars=[PillarOut(pillar=p, label=PILLARS[p]["label"], emoji=PILLARS[p]["emoji"]) for p in ctx.top_pillars],
    )


@router.get("/mood/options")
async def get_mood_options():
    return MOODS


@router.get("/mood", response_model=MoodOut)
async def get_today_mood(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    doc = await db.moods.find_one({"user_id": str(current_user["_id"]), "log_date": today})
    return MoodOut(mood=doc["mood"] if doc else None, log_date=today)


@router.post("/mood", response_model=MoodOut)
async def set_today_mood(
    payload: MoodIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if payload.mood not in MOODS:
        raise HTTPException(status_code=400, detail="Invalid mood")
    today = date.today().isoformat()
    await db.moods.update_one(
        {"user_id": str(current_user["_id"]), "log_date": today},
        {"$set": {"mood": payload.mood, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return MoodOut(mood=payload.mood, log_date=today)
