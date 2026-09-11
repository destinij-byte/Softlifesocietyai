from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])

CATEGORIES = {
    "money": {"label": "Money", "emoji": "💰"},
    "wellness": {"label": "Wellness", "emoji": "💪"},
    "career": {"label": "Career", "emoji": "💼"},
    "personal": {"label": "Personal", "emoji": "✨"},
}


class MilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class MilestoneOut(MilestoneIn):
    id: str
    done: bool = False


class GoalIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: str
    target: str = Field(min_length=1, max_length=160)
    deadline: str | None = None
    emoji: str = "🎯"


class GoalOut(GoalIn):
    id: str
    progress: float = 0
    milestones: list[MilestoneOut] = []
    created_at: datetime


def _validate_category(category: str) -> None:
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid goal category")


@router.get("/categories")
async def get_categories():
    return CATEGORIES


@router.get("", response_model=list[GoalOut])
async def list_goals(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.goals.find({"user_id": str(current_user["_id"])}).sort("created_at", -1)
    goals = await cursor.to_list(length=200)
    return [_serialize_goal(g) for g in goals]


def _serialize_goal(g: dict) -> GoalOut:
    return GoalOut(
        id=str(g["_id"]),
        title=g["title"],
        category=g["category"],
        target=g["target"],
        deadline=g.get("deadline"),
        emoji=g.get("emoji", "🎯"),
        progress=g.get("progress", 0),
        milestones=[MilestoneOut(id=m["id"], title=m["title"], done=m.get("done", False)) for m in g.get("milestones", [])],
        created_at=g["created_at"],
    )


@router.post("", response_model=GoalOut, status_code=201)
async def create_goal(
    payload: GoalIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_category(payload.category)
    doc = {
        "user_id": str(current_user["_id"]),
        **payload.model_dump(),
        "progress": 0,
        "milestones": [],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.goals.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_goal(doc)


@router.put("/{goal_id}/progress", response_model=GoalOut)
async def update_progress(
    goal_id: str,
    progress: float,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    progress = max(0.0, min(1.0, progress))
    result = await db.goals.find_one_and_update(
        {"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])},
        {"$set": {"progress": progress}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return _serialize_goal(result)


@router.post("/{goal_id}/milestones", response_model=GoalOut)
async def add_milestone(
    goal_id: str,
    payload: MilestoneIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    milestone = {"id": str(ObjectId()), "title": payload.title, "done": False}
    result = await db.goals.find_one_and_update(
        {"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])},
        {"$push": {"milestones": milestone}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return _serialize_goal(result)


@router.put("/{goal_id}/milestones/{milestone_id}/toggle", response_model=GoalOut)
async def toggle_milestone(
    goal_id: str,
    milestone_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    goal = await db.goals.find_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    milestones = goal.get("milestones", [])
    found = False
    for m in milestones:
        if m["id"] == milestone_id:
            m["done"] = not m.get("done", False)
            found = True
    if not found:
        raise HTTPException(status_code=404, detail="Milestone not found")

    await db.goals.update_one({"_id": goal["_id"]}, {"$set": {"milestones": milestones}})
    goal["milestones"] = milestones
    return _serialize_goal(goal)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.goals.delete_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    return None
