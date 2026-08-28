from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/challenges", tags=["challenges"])

SEED_CHALLENGES = [
    {
        "slug": "hydration-week",
        "title": "Hydration Week",
        "emoji": "💧",
        "description": "Drink 8 glasses of water a day, for 7 days straight.",
        "duration_days": 7,
    },
    {
        "slug": "morning-movement",
        "title": "10-Day Morning Movement",
        "emoji": "🌅",
        "description": "10 minutes of gentle movement every morning for 10 days.",
        "duration_days": 10,
    },
    {
        "slug": "gratitude-glow",
        "title": "Gratitude Glow-Up",
        "emoji": "🌷",
        "description": "Write down 3 things you're grateful for, every day for 5 days.",
        "duration_days": 5,
    },
    {
        "slug": "meal-prep-master",
        "title": "Meal Prep Master",
        "emoji": "🍱",
        "description": "Prep at least one meal ahead of time, 3 times this week.",
        "duration_days": 7,
    },
]


async def ensure_seed_challenges(db: AsyncIOMotorDatabase) -> None:
    count = await db.challenges.count_documents({})
    if count == 0:
        await db.challenges.insert_many([dict(c) for c in SEED_CHALLENGES])


@router.get("")
async def list_challenges(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await ensure_seed_challenges(db)
    challenges = await db.challenges.find({}).to_list(length=100)

    joined_cursor = db.challenge_participants.find({"user_id": str(current_user["_id"])})
    joined = await joined_cursor.to_list(length=100)
    joined_map = {j["challenge_slug"]: j for j in joined}

    result = []
    for c in challenges:
        participation = joined_map.get(c["slug"])
        result.append(
            {
                "slug": c["slug"],
                "title": c["title"],
                "emoji": c["emoji"],
                "description": c["description"],
                "duration_days": c["duration_days"],
                "joined": participation is not None,
                "completed": bool(participation and participation.get("completed")),
                "participant_count": await db.challenge_participants.count_documents({"challenge_slug": c["slug"]}),
            }
        )
    return result


@router.post("/{slug}/join")
async def join_challenge(
    slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await ensure_seed_challenges(db)
    challenge = await db.challenges.find_one({"slug": slug})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    now = datetime.now(timezone.utc)
    await db.challenge_participants.update_one(
        {"user_id": str(current_user["_id"]), "challenge_slug": slug},
        {
            "$setOnInsert": {
                "user_id": str(current_user["_id"]),
                "challenge_slug": slug,
                "joined_at": now,
                "ends_at": now + timedelta(days=challenge["duration_days"]),
                "completed": False,
            }
        },
        upsert=True,
    )
    return {"joined": True, "slug": slug}


@router.post("/{slug}/complete")
async def complete_challenge(
    slug: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db.challenge_participants.update_one(
        {"user_id": str(current_user["_id"]), "challenge_slug": slug},
        {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="You haven't joined this challenge yet")
    return {"completed": True, "slug": slug}
