from datetime import date, datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/nutrition", tags=["nutrition"])

MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")


class FoodLogIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    calories: int = Field(ge=0, le=10000)
    meal_type: str = "snack"
    emoji: str = "🍽️"


class FoodLogOut(FoodLogIn):
    id: str
    logged_at: datetime


class DailySummary(BaseModel):
    date: str
    total_calories: int
    goal_calories: int
    entries: list[FoodLogOut]


DAILY_GOAL_CALORIES = 2000


@router.get("/goal")
async def get_goal(current_user: dict = Depends(get_current_user)):
    return {"goal_calories": current_user.get("calorie_goal", DAILY_GOAL_CALORIES)}


@router.put("/goal")
async def set_goal(
    goal_calories: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"calorie_goal": goal_calories}})
    return {"goal_calories": goal_calories}


@router.get("/today", response_model=DailySummary)
async def get_today(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    cursor = db.food_logs.find({"user_id": str(current_user["_id"]), "log_date": today}).sort("logged_at", 1)
    entries_raw = await cursor.to_list(length=200)
    entries = [FoodLogOut(id=str(e["_id"]), **{k: e[k] for k in ("name", "calories", "meal_type", "emoji", "logged_at")}) for e in entries_raw]
    total = sum(e.calories for e in entries)
    return DailySummary(
        date=today,
        total_calories=total,
        goal_calories=current_user.get("calorie_goal", DAILY_GOAL_CALORIES),
        entries=entries,
    )


@router.post("/entries", response_model=FoodLogOut, status_code=201)
async def add_entry(
    payload: FoodLogIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if payload.meal_type not in MEAL_TYPES:
        raise HTTPException(status_code=400, detail="Invalid meal_type")

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": str(current_user["_id"]),
        "name": payload.name,
        "calories": payload.calories,
        "meal_type": payload.meal_type,
        "emoji": payload.emoji,
        "logged_at": now,
        "log_date": now.date().isoformat(),
    }
    result = await db.food_logs.insert_one(doc)
    return FoodLogOut(id=str(result.inserted_id), **payload.model_dump(), logged_at=now)


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.food_logs.delete_one({"_id": ObjectId(entry_id), "user_id": str(current_user["_id"])})
    return None
