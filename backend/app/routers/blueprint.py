from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.blueprint import BlueprintIn, BlueprintOut
from app.schemas.pillars import ERAS, PILLARS

router = APIRouter(prefix="/blueprint", tags=["blueprint"])


@router.get("/pillars")
async def get_pillars():
    return PILLARS


@router.get("/eras")
async def get_eras():
    return ERAS


def _empty_blueprint(now: datetime) -> dict:
    return {
        "era": None,
        "current_state": "",
        "becoming": "",
        "pillars": [],
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
        "created_at": created_at,
        "updated_at": now,
    }
    await db.blueprints.update_one({"user_id": user_id}, {"$set": update}, upsert=True)
    return BlueprintOut(**{k: v for k, v in update.items() if k != "user_id"})
