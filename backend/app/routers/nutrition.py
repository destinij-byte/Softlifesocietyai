import base64
from datetime import date, datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user
from app.services.food_database import search_foods
from app.services.nourish_ai import analyze_meal_photo, build_meal_suggestion

router = APIRouter(prefix="/nourish", tags=["nourish"])

MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")

DEFAULT_GOALS = {"calorie_goal": 1650, "protein_goal_g": 120, "carbs_goal_g": 165, "fat_goal_g": 55}


class FoodLogIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    calories: int = Field(ge=0, le=10000)
    protein_g: float = Field(default=0, ge=0, le=1000)
    carbs_g: float = Field(default=0, ge=0, le=1000)
    fat_g: float = Field(default=0, ge=0, le=1000)
    meal_type: str = "snack"
    emoji: str = "🍽️"


class FoodLogOut(FoodLogIn):
    id: str
    logged_at: datetime


class DailySummary(BaseModel):
    date: str
    total_calories: int
    goal_calories: int
    total_protein_g: float
    goal_protein_g: float
    total_carbs_g: float
    goal_carbs_g: float
    total_fat_g: float
    goal_fat_g: float
    entries: list[FoodLogOut]


class FoodResult(BaseModel):
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    emoji: str


class MealSuggestion(BaseModel):
    name: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    emoji: str
    description: str | None = None
    note: str | None = None


def _goal(user: dict) -> dict:
    return {
        "calorie_goal": user.get("calorie_goal", DEFAULT_GOALS["calorie_goal"]),
        "protein_goal_g": user.get("protein_goal_g", DEFAULT_GOALS["protein_goal_g"]),
        "carbs_goal_g": user.get("carbs_goal_g", DEFAULT_GOALS["carbs_goal_g"]),
        "fat_goal_g": user.get("fat_goal_g", DEFAULT_GOALS["fat_goal_g"]),
    }


@router.get("/goal")
async def get_goal(current_user: dict = Depends(get_current_user)):
    return _goal(current_user)


@router.put("/goal")
async def set_goal(
    calorie_goal: int,
    protein_goal_g: float = DEFAULT_GOALS["protein_goal_g"],
    carbs_goal_g: float = DEFAULT_GOALS["carbs_goal_g"],
    fat_goal_g: float = DEFAULT_GOALS["fat_goal_g"],
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    update = {
        "calorie_goal": calorie_goal,
        "protein_goal_g": protein_goal_g,
        "carbs_goal_g": carbs_goal_g,
        "fat_goal_g": fat_goal_g,
    }
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": update})
    return update


@router.get("/today", response_model=DailySummary)
async def get_today(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    cursor = db.food_logs.find({"user_id": str(current_user["_id"]), "log_date": today}).sort("logged_at", 1)
    entries_raw = await cursor.to_list(length=200)
    fields = ("name", "calories", "protein_g", "carbs_g", "fat_g", "meal_type", "emoji", "logged_at")
    entries = [FoodLogOut(id=str(e["_id"]), **{k: e.get(k, 0) for k in fields}) for e in entries_raw]
    goal = _goal(current_user)

    return DailySummary(
        date=today,
        total_calories=sum(e.calories for e in entries),
        goal_calories=goal["calorie_goal"],
        total_protein_g=sum(e.protein_g for e in entries),
        goal_protein_g=goal["protein_goal_g"],
        total_carbs_g=sum(e.carbs_g for e in entries),
        goal_carbs_g=goal["carbs_goal_g"],
        total_fat_g=sum(e.fat_g for e in entries),
        goal_fat_g=goal["fat_goal_g"],
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
        **payload.model_dump(),
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


@router.get("/search", response_model=list[FoodResult])
async def search(q: str = Query(""), current_user: dict = Depends(get_current_user)):
    return search_foods(q)


@router.post("/analyze-meal", response_model=MealSuggestion)
async def analyze_meal(
    photo: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    image_bytes = await photo.read()
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB)")

    media_type = photo.content_type or "image/jpeg"
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    result = await analyze_meal_photo(image_b64, media_type)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Meal photo analysis isn't available right now — try Search Food or Manual Entry instead.",
        )
    return MealSuggestion(**result)


@router.post("/meal-builder", response_model=MealSuggestion)
async def meal_builder(
    meal_type: str = Query("dinner"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    entries = await db.food_logs.find({"user_id": str(current_user["_id"]), "log_date": today}).to_list(length=200)
    goal = _goal(current_user)
    remaining_calories = goal["calorie_goal"] - sum(e["calories"] for e in entries)
    remaining_protein = goal["protein_goal_g"] - sum(e.get("protein_g", 0) for e in entries)

    suggestion = await build_meal_suggestion(max(remaining_calories, 0), max(remaining_protein, 0), meal_type)
    return MealSuggestion(**suggestion)


WATER_GOAL_GLASSES = 8


class WaterOut(BaseModel):
    count: int
    goal: int = WATER_GOAL_GLASSES


@router.get("/water", response_model=WaterOut)
async def get_water(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    doc = await db.water_logs.find_one({"user_id": str(current_user["_id"]), "log_date": today})
    return WaterOut(count=doc["count"] if doc else 0)


@router.post("/water/add", response_model=WaterOut)
async def add_water(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    doc = await db.water_logs.find_one_and_update(
        {"user_id": str(current_user["_id"]), "log_date": today},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True,
    )
    return WaterOut(count=doc["count"])


@router.post("/water/remove", response_model=WaterOut)
async def remove_water(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    today = date.today().isoformat()
    doc = await db.water_logs.find_one({"user_id": str(current_user["_id"]), "log_date": today})
    current = doc["count"] if doc else 0
    new_count = max(0, current - 1)
    await db.water_logs.update_one(
        {"user_id": str(current_user["_id"]), "log_date": today},
        {"$set": {"count": new_count}},
        upsert=True,
    )
    return WaterOut(count=new_count)
