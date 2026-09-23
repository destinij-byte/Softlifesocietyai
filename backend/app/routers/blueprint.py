from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.blueprint import BlueprintIn, BlueprintOut, NutritionPreferences
from app.schemas.pillars import ERAS, PILLARS
from app.schemas.personalization import (
    AFFIRMATION_CATEGORIES,
    COACHING_STYLES,
    DIETARY_STYLES,
    MANIFESTATION_CATEGORIES,
    MOTIVATION_STYLES,
)

router = APIRouter(prefix="/blueprint", tags=["blueprint"])


@router.get("/pillars")
async def get_pillars():
    return PILLARS


@router.get("/eras")
async def get_eras():
    return ERAS


@router.get("/coaching-styles")
async def get_coaching_styles():
    return COACHING_STYLES


@router.get("/motivation-styles")
async def get_motivation_styles():
    return MOTIVATION_STYLES


@router.get("/affirmation-categories")
async def get_affirmation_categories():
    return AFFIRMATION_CATEGORIES


@router.get("/manifestation-categories")
async def get_manifestation_categories():
    return MANIFESTATION_CATEGORIES


@router.get("/dietary-styles")
async def get_dietary_styles():
    return DIETARY_STYLES


def _empty_blueprint(now: datetime) -> dict:
    return {
        "era": None,
        "current_state": "",
        "becoming": "",
        "pillars": [],
        "preferred_name": None,
        "coaching_style": None,
        "motivation_style": None,
        "affirmation_categories": [],
        "manifestation_categories": [],
        "nutrition_preferences": NutritionPreferences(),
        "created_at": now,
        "updated_at": now,
    }


@router.get("", response_model=BlueprintOut)
async def get_blueprint(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """A user with no Blueprint yet gets an empty, editable one rather than a
    404 — there's exactly one Blueprint per user, so there's nothing to pick
    between, and the frontend can render the same form either way."""
    doc = await db.blueprints.find_one({"user_id": str(current_user["_id"])})
    if doc is None:
        return BlueprintOut(**_empty_blueprint(datetime.now(timezone.utc)))
    return BlueprintOut(
        era=doc.get("era"),
        current_state=doc.get("current_state", ""),
        becoming=doc.get("becoming", ""),
        pillars=doc.get("pillars", []),
        preferred_name=doc.get("preferred_name"),
        coaching_style=doc.get("coaching_style"),
        motivation_style=doc.get("motivation_style"),
        affirmation_categories=doc.get("affirmation_categories", []),
        manifestation_categories=doc.get("manifestation_categories", []),
        nutrition_preferences=doc.get("nutrition_preferences", NutritionPreferences()),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.put("", response_model=BlueprintOut)
async def put_blueprint(
    payload: BlueprintIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user_id = str(current_user["_id"])
    now = datetime.now(timezone.utc)
    existing = await db.blueprints.find_one({"user_id": user_id})
    created_at = existing["created_at"] if existing else now

    update = {
        "user_id": user_id,
        "era": payload.era,
        "current_state": payload.current_state.strip(),
        "becoming": payload.becoming.strip(),
        "pillars": [p.model_dump() for p in payload.pillars],
        "preferred_name": payload.preferred_name.strip() if payload.preferred_name else None,
        "coaching_style": payload.coaching_style,
        "motivation_style": payload.motivation_style,
        "affirmation_categories": payload.affirmation_categories,
        "manifestation_categories": payload.manifestation_categories,
        "nutrition_preferences": payload.nutrition_preferences.model_dump(),
        "created_at": created_at,
        "updated_at": now,
    }
    await db.blueprints.update_one({"user_id": user_id}, {"$set": update}, upsert=True)
    return BlueprintOut(**{k: v for k, v in update.items() if k != "user_id"})
