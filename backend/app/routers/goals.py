import base64
import io
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.pillars import PILLARS, is_valid_pillar

router = APIRouter(prefix="/goals", tags=["goals"])

CATEGORIES = {
    "money": {"label": "Money", "emoji": "💰"},
    "wellness": {"label": "Wellness", "emoji": "💪"},
    "career": {"label": "Career", "emoji": "💼"},
    "personal": {"label": "Personal", "emoji": "✨"},
}

TIMEFRAMES = {
    "none": {"label": "No timeframe", "emoji": "🎯"},
    "quarterly": {"label": "Quarterly Goal", "emoji": "🗓️"},
    "long_term": {"label": "Long-Term Vision", "emoji": "🌠"},
}

MAX_VISION_IMAGES = 12
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
VISION_IMAGE_MAX_DIMENSION = 1080


class MilestoneIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class MilestoneOut(MilestoneIn):
    id: str
    done: bool = False


class VisionImageOut(BaseModel):
    id: str
    image: str
    caption: str | None = None
    created_at: datetime


class BreakdownItem(BaseModel):
    """One step in a Smart Goal's target -> monthly -> weekly -> today
    decomposition. `period` says which level of the breakdown this is."""

    id: str
    period: str  # "monthly" | "weekly" | "today"
    label: str = Field(min_length=1, max_length=200)
    target: float | None = None
    done: bool = False


class BreakdownIn(BaseModel):
    period: str
    label: str = Field(min_length=1, max_length=200)
    target: float | None = None


class GoalIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    category: str
    target: str = Field(min_length=1, max_length=160)
    deadline: str | None = None
    emoji: str = "🎯"
    timeframe: str = "none"
    pillar: str | None = None
    why: str | None = Field(default=None, max_length=400)
    target_value: float | None = None


class GoalOut(GoalIn):
    id: str
    progress: float = 0
    milestones: list[MilestoneOut] = []
    vision_images: list[VisionImageOut] = []
    breakdown: list[BreakdownItem] = []
    created_at: datetime


def _validate_category(category: str) -> None:
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid goal category")


def _validate_timeframe(timeframe: str) -> None:
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=400, detail="Invalid goal timeframe")


def _validate_pillar(pillar: str | None) -> None:
    if pillar is not None and not is_valid_pillar(pillar):
        raise HTTPException(status_code=400, detail="Invalid pillar")


def _validate_breakdown_period(period: str) -> None:
    if period not in ("monthly", "weekly", "today"):
        raise HTTPException(status_code=400, detail="period must be monthly, weekly, or today")


def _compress_image(image_bytes: bytes, content_type: str | None) -> str:
    """Downscale + re-encode an uploaded photo and return a data: URI, so
    vision-board collages stay light in Mongo and fast to load on-device."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        img.thumbnail((VISION_IMAGE_MAX_DIMENSION, VISION_IMAGE_MAX_DIMENSION))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=78)
        encoded = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        # Fall back to storing the original bytes as-is if Pillow isn't
        # available or the image can't be decoded.
        media_type = content_type or "image/jpeg"
        encoded = base64.standard_b64encode(image_bytes).decode("utf-8")
        return f"data:{media_type};base64,{encoded}"


@router.get("/categories")
async def get_categories():
    return CATEGORIES


@router.get("/timeframes")
async def get_timeframes():
    return TIMEFRAMES


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
        timeframe=g.get("timeframe", "none"),
        pillar=g.get("pillar"),
        why=g.get("why"),
        target_value=g.get("target_value"),
        progress=g.get("progress", 0),
        milestones=[MilestoneOut(id=m["id"], title=m["title"], done=m.get("done", False)) for m in g.get("milestones", [])],
        vision_images=[
            VisionImageOut(id=v["id"], image=v["image"], caption=v.get("caption"), created_at=v["created_at"])
            for v in g.get("vision_images", [])
        ],
        breakdown=[
            BreakdownItem(id=b["id"], period=b["period"], label=b["label"], target=b.get("target"), done=b.get("done", False))
            for b in g.get("breakdown", [])
        ],
        created_at=g["created_at"],
    )


@router.post("", response_model=GoalOut, status_code=201)
async def create_goal(
    payload: GoalIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_category(payload.category)
    _validate_timeframe(payload.timeframe)
    _validate_pillar(payload.pillar)
    doc = {
        "user_id": str(current_user["_id"]),
        **payload.model_dump(),
        "progress": 0,
        "milestones": [],
        "vision_images": [],
        "breakdown": [],
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


@router.post("/{goal_id}/breakdown", response_model=GoalOut)
async def add_breakdown_item(
    goal_id: str,
    payload: BreakdownIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Adds one step of the goal's target -> monthly -> weekly -> today
    decomposition. A later phase lets Luna propose a full breakdown for the
    user to approve; this endpoint is the CRUD layer either path writes
    through, and is usable standalone today for a user who builds her own."""
    _validate_breakdown_period(payload.period)
    item = {"id": str(ObjectId()), "period": payload.period, "label": payload.label, "target": payload.target, "done": False}
    result = await db.goals.find_one_and_update(
        {"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])},
        {"$push": {"breakdown": item}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found")
    return _serialize_goal(result)


@router.put("/{goal_id}/breakdown/{item_id}/toggle", response_model=GoalOut)
async def toggle_breakdown_item(
    goal_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    goal = await db.goals.find_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    breakdown = goal.get("breakdown", [])
    found = False
    for item in breakdown:
        if item["id"] == item_id:
            item["done"] = not item.get("done", False)
            found = True
    if not found:
        raise HTTPException(status_code=404, detail="Breakdown item not found")

    await db.goals.update_one({"_id": goal["_id"]}, {"$set": {"breakdown": breakdown}})
    goal["breakdown"] = breakdown
    return _serialize_goal(goal)


@router.delete("/{goal_id}/breakdown/{item_id}", response_model=GoalOut)
async def delete_breakdown_item(
    goal_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    goal = await db.goals.find_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal["breakdown"] = [item for item in goal.get("breakdown", []) if item["id"] != item_id]
    await db.goals.update_one({"_id": goal["_id"]}, {"$set": {"breakdown": goal["breakdown"]}})
    return _serialize_goal(goal)


@router.post("/{goal_id}/vision-images", response_model=GoalOut)
async def add_vision_image(
    goal_id: str,
    photo: UploadFile = File(...),
    caption: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Add a photo to a goal's vision board collage — meant for goals with a
    quarterly or long-term timeframe, so she can build out what she's manifesting."""
    goal = await db.goals.find_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if len(goal.get("vision_images", [])) >= MAX_VISION_IMAGES:
        raise HTTPException(status_code=400, detail=f"Vision boards are capped at {MAX_VISION_IMAGES} photos for now")

    image_bytes = await photo.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB)")

    image_data_uri = _compress_image(image_bytes, photo.content_type)
    entry = {
        "id": str(ObjectId()),
        "image": image_data_uri,
        "caption": caption.strip() if caption else None,
        "created_at": datetime.now(timezone.utc),
    }
    await db.goals.update_one({"_id": goal["_id"]}, {"$push": {"vision_images": entry}})
    goal.setdefault("vision_images", []).append(entry)
    return _serialize_goal(goal)


@router.delete("/{goal_id}/vision-images/{image_id}", response_model=GoalOut)
async def delete_vision_image(
    goal_id: str,
    image_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    goal = await db.goals.find_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal["vision_images"] = [v for v in goal.get("vision_images", []) if v["id"] != image_id]
    await db.goals.update_one({"_id": goal["_id"]}, {"$set": {"vision_images": goal["vision_images"]}})
    return _serialize_goal(goal)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    await db.goals.delete_one({"_id": ObjectId(goal_id), "user_id": str(current_user["_id"])})
    return None
