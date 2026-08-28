from datetime import date, datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/workouts", tags=["workouts"])


class WorkoutIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    workout_type: str = "movement"
    duration_minutes: int = Field(ge=1, le=600)
    emoji: str = "🏋️‍♀️"
    notes: str | None = None


class WorkoutOut(WorkoutIn):
    id: str
    logged_at: datetime


@router.get("", response_model=list[WorkoutOut])
async def list_workouts(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.workouts.find({"user_id": str(current_user["_id"])}).sort("logged_at", -1)
    workouts = await cursor.to_list(length=200)
    return [
        WorkoutOut(
            id=str(w["_id"]),
            **{k: w[k] for k in ("name", "workout_type", "duration_minutes", "emoji", "logged_at")},
            notes=w.get("notes"),
        )
        for w in workouts
    ]


@router.get("/streak")
async def get_streak(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.workouts.find({"user_id": str(current_user["_id"])}).sort("logged_at", -1)
    workouts = await cursor.to_list(length=400)
    dates = sorted({w["logged_at"].date() for w in workouts}, reverse=True)

    streak = 0
    expected = date.today()
    for d in dates:
        if d == expected:
            streak += 1
            expected = expected.fromordinal(expected.toordinal() - 1)
        elif d < expected:
            break

    return {"streak_days": streak, "total_workouts": len(workouts)}


@router.post("", response_model=WorkoutOut, status_code=201)
async def log_workout(
    payload: WorkoutIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    doc = {"user_id": str(current_user["_id"]), **payload.model_dump(), "logged_at": now}
    result = await db.workouts.insert_one(doc)
    return WorkoutOut(id=str(result.inserted_id), **payload.model_dump(), logged_at=now)


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.workouts.delete_one({"_id": ObjectId(workout_id), "user_id": str(current_user["_id"])})
    return None
