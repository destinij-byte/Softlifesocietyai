from datetime import date, datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/routines", tags=["routines"])

DEFAULT_STEPS = {
    "morning": [
        "Wake up 🌅",
        "Drink water 💧",
        "Hygiene 🪥",
        "Skincare 🧴",
        "Make bed 🛏️",
        "Movement 🧘‍♀️",
        "Breakfast 🍓",
        "Review goals 🎯",
    ],
    "night": [
        "Skincare 🧴",
        "Journal 📓",
        "Tidy space 🕯️",
        "Screens off 📵",
        "Read 📖",
        "Gratitude 🤍",
    ],
}


class StepIn(BaseModel):
    label: str = Field(min_length=1, max_length=160)


class StepOut(StepIn):
    id: str
    done: bool = False


class RoutineOut(BaseModel):
    type: str
    steps: list[StepOut]


async def _ensure_routine(db: AsyncIOMotorDatabase, user_id: str, routine_type: str) -> dict:
    routine = await db.routines.find_one({"user_id": user_id, "type": routine_type})
    today = date.today().isoformat()

    if not routine:
        steps = [{"id": str(ObjectId()), "label": label, "done": False} for label in DEFAULT_STEPS[routine_type]]
        doc = {"user_id": user_id, "type": routine_type, "steps": steps, "reset_date": today}
        result = await db.routines.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    if routine.get("reset_date") != today:
        for step in routine["steps"]:
            step["done"] = False
        await db.routines.update_one({"_id": routine["_id"]}, {"$set": {"steps": routine["steps"], "reset_date": today}})

    return routine


def _validate_type(routine_type: str) -> None:
    if routine_type not in DEFAULT_STEPS:
        raise HTTPException(status_code=400, detail="routine type must be 'morning' or 'night'")


@router.get("/{routine_type}", response_model=RoutineOut)
async def get_routine(
    routine_type: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(routine_type)
    routine = await _ensure_routine(db, str(current_user["_id"]), routine_type)
    return RoutineOut(type=routine_type, steps=[StepOut(**s) for s in routine["steps"]])


@router.post("/{routine_type}/steps", response_model=RoutineOut)
async def add_step(
    routine_type: str,
    payload: StepIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(routine_type)
    user_id = str(current_user["_id"])
    routine = await _ensure_routine(db, user_id, routine_type)
    step = {"id": str(ObjectId()), "label": payload.label, "done": False}
    await db.routines.update_one({"_id": routine["_id"]}, {"$push": {"steps": step}})
    routine["steps"].append(step)
    return RoutineOut(type=routine_type, steps=[StepOut(**s) for s in routine["steps"]])


@router.put("/{routine_type}/steps/{step_id}/toggle", response_model=RoutineOut)
async def toggle_step(
    routine_type: str,
    step_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(routine_type)
    user_id = str(current_user["_id"])
    routine = await _ensure_routine(db, user_id, routine_type)

    found = False
    for step in routine["steps"]:
        if step["id"] == step_id:
            step["done"] = not step.get("done", False)
            found = True
    if not found:
        raise HTTPException(status_code=404, detail="Step not found")

    await db.routines.update_one({"_id": routine["_id"]}, {"$set": {"steps": routine["steps"]}})
    return RoutineOut(type=routine_type, steps=[StepOut(**s) for s in routine["steps"]])


@router.delete("/{routine_type}/steps/{step_id}", response_model=RoutineOut)
async def delete_step(
    routine_type: str,
    step_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(routine_type)
    user_id = str(current_user["_id"])
    routine = await _ensure_routine(db, user_id, routine_type)
    routine["steps"] = [s for s in routine["steps"] if s["id"] != step_id]
    await db.routines.update_one({"_id": routine["_id"]}, {"$set": {"steps": routine["steps"]}})
    return RoutineOut(type=routine_type, steps=[StepOut(**s) for s in routine["steps"]])
