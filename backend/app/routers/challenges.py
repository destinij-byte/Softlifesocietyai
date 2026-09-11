from datetime import date, datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/challenges", tags=["challenges"])

INTENSITIES = {
    "hard": {"label": "Hard", "emoji": "🔥"},
    "medium": {"label": "Medium", "emoji": "🌤"},
    "easy": {"label": "Easy", "emoji": "🌱"},
}

TEMPLATES = [
    {"slug": "75-day", "title": "75 Day Challenge", "emoji": "🏔️", "duration_days": 75, "needs_intensity": True},
    {"slug": "45-day", "title": "45 Day Challenge", "emoji": "⛰️", "duration_days": 45, "needs_intensity": True},
    {"slug": "30-day", "title": "30 Day Challenge", "emoji": "🌄", "duration_days": 30, "needs_intensity": True},
    {"slug": "water-intake", "title": "Water Intake", "emoji": "💧", "duration_days": 9999, "needs_intensity": False, "description": "8 glasses of water a day."},
    {"slug": "10k-steps", "title": "10,000 Steps Daily", "emoji": "🚶‍♀️", "duration_days": 9999, "needs_intensity": False, "description": "Hit 10,000 steps every day."},
]


class JoinRequest(BaseModel):
    intensity: str | None = None


@router.get("/templates")
async def list_templates():
    return TEMPLATES


@router.get("/intensities")
async def list_intensities():
    return INTENSITIES


def _template(slug: str) -> dict:
    template = next((t for t in TEMPLATES if t["slug"] == slug), None)
    if not template:
        raise HTTPException(status_code=404, detail="Challenge template not found")
    return template


@router.post("/{slug}/join")
async def join_challenge(
    slug: str,
    payload: JoinRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    template = _template(slug)
    if template["needs_intensity"] and payload.intensity not in INTENSITIES:
        raise HTTPException(status_code=400, detail="This challenge needs an intensity: hard, medium, or easy")

    now = datetime.now(timezone.utc)
    existing = await db.challenge_participants.find_one({"user_id": str(current_user["_id"]), "slug": slug, "active": True})
    if existing:
        raise HTTPException(status_code=409, detail="You're already doing this challenge")

    doc = {
        "user_id": str(current_user["_id"]),
        "slug": slug,
        "intensity": payload.intensity,
        "joined_at": now,
        "duration_days": template["duration_days"],
        "log_dates": [],
        "points": 0,
        "streak": 0,
        "active": True,
    }
    await db.challenge_participants.insert_one(doc)
    return {"joined": True, "slug": slug}


@router.get("/mine")
async def my_challenges(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    participations = await db.challenge_participants.find(
        {"user_id": str(current_user["_id"]), "active": True}
    ).to_list(length=50)

    result = []
    today = date.today().isoformat()
    for p in participations:
        template = _template(p["slug"])
        day_count = len(p.get("log_dates", []))
        result.append(
            {
                "slug": p["slug"],
                "title": template["title"],
                "emoji": template["emoji"],
                "intensity": p.get("intensity"),
                "duration_days": p["duration_days"],
                "day_count": day_count,
                "streak": p.get("streak", 0),
                "points": p.get("points", 0),
                "logged_today": today in p.get("log_dates", []),
                "progress": min(1.0, day_count / p["duration_days"]) if p["duration_days"] < 9999 else 0,
            }
        )
    return result


@router.post("/{slug}/log-today")
async def log_today(
    slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    participation = await db.challenge_participants.find_one(
        {"user_id": str(current_user["_id"]), "slug": slug, "active": True}
    )
    if not participation:
        raise HTTPException(status_code=404, detail="You haven't joined this challenge")

    today = date.today()
    today_str = today.isoformat()
    log_dates = participation.get("log_dates", [])
    if today_str in log_dates:
        raise HTTPException(status_code=409, detail="Already logged today")

    log_dates.append(today_str)
    yesterday_str = (today - timedelta(days=1)).isoformat()
    streak = participation.get("streak", 0) + 1 if yesterday_str in log_dates else 1
    points = participation.get("points", 0) + 10

    await db.challenge_participants.update_one(
        {"_id": participation["_id"]},
        {"$set": {"log_dates": log_dates, "streak": streak, "points": points}},
    )
    return {"logged": True, "streak": streak, "points": points}


@router.get("/leaderboard")
async def leaderboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    friend_ids = current_user.get("friend_ids", [])
    member_ids = [current_user["_id"]] + [ObjectId(fid) for fid in friend_ids]
    members = await db.users.find({"_id": {"$in": member_ids}}).to_list(length=200)

    rows = []
    for member in members:
        member_id = str(member["_id"])
        participations = await db.challenge_participants.find({"user_id": member_id, "active": True}).to_list(length=50)
        total_points = sum(p.get("points", 0) for p in participations)
        best_streak = max((p.get("streak", 0) for p in participations), default=0)
        rows.append(
            {
                "id": member_id,
                "name": member["name"],
                "avatar_emoji": member.get("avatar_emoji", "🌸"),
                "points": total_points,
                "streak": best_streak,
                "is_you": member_id == str(current_user["_id"]),
            }
        )

    rows.sort(key=lambda r: (-r["points"], -r["streak"]))
    for i, row in enumerate(rows):
        row["rank"] = i + 1
    return rows
