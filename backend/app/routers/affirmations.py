from datetime import date, datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.personalization import AFFIRMATION_CATEGORIES, COACHING_STYLES
from app.schemas.pillars import PILLARS
from app.services.affirmation_ai import generate_affirmation
from app.services.ai_client import get_ai_client
from app.services.alignment import get_alignment
from app.services.blueprint_context import get_blueprint_context

router = APIRouter(prefix="/affirmations", tags=["affirmations"])

MANIFESTATION_PROMPTS = {
    "morning": [
        "What am I calling into my life today?",
        "If today went exactly how I wanted, what would that look like?",
        "What version of me is walking into this day?",
        "What am I most grateful is already on its way to me?",
        "What would I do today if I already believed it was working?",
    ],
    "night": [
        "What moment today am I most grateful for?",
        "What did today teach me about the woman I'm becoming?",
        "What am I ready to release before I sleep?",
        "What's one sign today that things are working out for me?",
        "What do I want to wake up already believing tomorrow?",
    ],
}

MAX_HISTORY = 30


class CustomAffirmationIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class CustomAffirmationOut(CustomAffirmationIn):
    id: str


class JournalIn(BaseModel):
    text: str = Field(default="", max_length=2000)


class AffirmationHistoryOut(BaseModel):
    id: str
    text: str
    category: str | None
    favorited: bool
    created_at: datetime


class AffirmationStateOut(BaseModel):
    type: str
    daily_affirmation: str
    daily_affirmation_id: str
    daily_affirmation_category: str | None
    daily_affirmation_favorited: bool
    manifestation_prompt: str
    custom: list[CustomAffirmationOut] = []
    journal_entry: str = ""


class RegenerateIn(BaseModel):
    category: str | None = None
    coaching_style: str | None = None

    @field_validator("category")
    @classmethod
    def _check_category(cls, value: str | None) -> str | None:
        if value is not None and value not in AFFIRMATION_CATEGORIES:
            raise ValueError("Unknown affirmation category")
        return value

    @field_validator("coaching_style")
    @classmethod
    def _check_coaching_style(cls, value: str | None) -> str | None:
        if value is not None and value not in COACHING_STYLES:
            raise ValueError("Unknown coaching style")
        return value


def _validate_type(affirmation_type: str) -> None:
    if affirmation_type not in ("morning", "night"):
        raise HTTPException(status_code=400, detail="type must be 'morning' or 'night'")


def _daily_pick(items: list[str]) -> str:
    day_index = date.today().timetuple().tm_yday
    return items[day_index % len(items)]


async def _get_or_create(db: AsyncIOMotorDatabase, user_id: str, affirmation_type: str) -> dict:
    doc = await db.affirmations.find_one({"user_id": user_id, "type": affirmation_type})
    if not doc:
        doc = {"user_id": user_id, "type": affirmation_type, "custom": [], "journal": {"date": "", "text": ""}}
        result = await db.affirmations.insert_one(doc)
        doc["_id"] = result.inserted_id
    return doc


async def _generate_and_save(
    db: AsyncIOMotorDatabase, user: dict, affirmation_type: str, category_override: str | None, coaching_style_override: str | None
) -> dict:
    """Personalized against the Blueprint (era, top pillars, becoming,
    coaching style, default affirmation categories) and, only when an AI
    call will actually happen, this week's Alignment 'why' as a lightweight
    signal of recent progress — never a single global day-of-year rotation."""
    user_id = str(user["_id"])
    ctx = await get_blueprint_context(db, user_id)
    category = category_override or (ctx.affirmation_categories[0] if ctx.affirmation_categories else None)
    coaching_style = coaching_style_override or ctx.coaching_style

    alignment_why = None
    if get_ai_client() is not None:
        alignment = await get_alignment(db, user)
        alignment_why = alignment.why

    top_pillar_labels = [PILLARS[p]["label"] for p in ctx.top_pillars if p in PILLARS]

    text = await generate_affirmation(
        category=category,
        coaching_style=coaching_style,
        era_label=ctx.era_label,
        top_pillar_labels=top_pillar_labels,
        becoming=ctx.becoming,
        alignment_why=alignment_why,
    )

    doc = {
        "user_id": user_id,
        "type": affirmation_type,
        "text": text,
        "category": category,
        "favorited": False,
        "log_date": date.today().isoformat(),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.affirmation_history.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def _get_or_generate_daily(db: AsyncIOMotorDatabase, user: dict, affirmation_type: str) -> dict:
    today = date.today().isoformat()
    existing = await db.affirmation_history.find_one(
        {"user_id": str(user["_id"]), "type": affirmation_type, "log_date": today},
        sort=[("created_at", -1)],
    )
    if existing:
        return existing
    return await _generate_and_save(db, user, affirmation_type, category_override=None, coaching_style_override=None)


def _serialize(doc: dict, affirmation_type: str, daily: dict) -> AffirmationStateOut:
    journal = doc.get("journal", {})
    today = date.today().isoformat()
    journal_entry = journal.get("text", "") if journal.get("date") == today else ""

    return AffirmationStateOut(
        type=affirmation_type,
        daily_affirmation=daily["text"],
        daily_affirmation_id=str(daily["_id"]),
        daily_affirmation_category=daily.get("category"),
        daily_affirmation_favorited=daily.get("favorited", False),
        manifestation_prompt=_daily_pick(MANIFESTATION_PROMPTS[affirmation_type]),
        custom=[CustomAffirmationOut(id=c["id"], text=c["text"]) for c in doc.get("custom", [])],
        journal_entry=journal_entry,
    )


@router.get("/{affirmation_type}", response_model=AffirmationStateOut)
async def get_affirmations(
    affirmation_type: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    doc = await _get_or_create(db, str(current_user["_id"]), affirmation_type)
    daily = await _get_or_generate_daily(db, current_user, affirmation_type)
    return _serialize(doc, affirmation_type, daily)


@router.post("/{affirmation_type}/regenerate", response_model=AffirmationStateOut)
async def regenerate_affirmation(
    affirmation_type: str,
    payload: RegenerateIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    doc = await _get_or_create(db, str(current_user["_id"]), affirmation_type)
    daily = await _generate_and_save(db, current_user, affirmation_type, payload.category, payload.coaching_style)
    return _serialize(doc, affirmation_type, daily)


@router.get("/{affirmation_type}/history", response_model=list[AffirmationHistoryOut])
async def get_affirmation_history(
    affirmation_type: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    cursor = db.affirmation_history.find(
        {"user_id": str(current_user["_id"]), "type": affirmation_type}
    ).sort("created_at", -1)
    entries = await cursor.to_list(length=MAX_HISTORY)
    return [
        AffirmationHistoryOut(id=str(e["_id"]), text=e["text"], category=e.get("category"), favorited=e.get("favorited", False), created_at=e["created_at"])
        for e in entries
    ]


@router.put("/{affirmation_type}/history/{history_id}/favorite", response_model=AffirmationHistoryOut)
async def toggle_favorite(
    affirmation_type: str,
    history_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    try:
        object_id = ObjectId(history_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid affirmation id")

    entry = await db.affirmation_history.find_one({"_id": object_id, "user_id": str(current_user["_id"])})
    if not entry:
        raise HTTPException(status_code=404, detail="Affirmation not found")

    updated = not entry.get("favorited", False)
    await db.affirmation_history.update_one({"_id": object_id}, {"$set": {"favorited": updated}})
    return AffirmationHistoryOut(id=str(object_id), text=entry["text"], category=entry.get("category"), favorited=updated, created_at=entry["created_at"])


@router.post("/{affirmation_type}/custom", response_model=AffirmationStateOut)
async def add_custom_affirmation(
    affirmation_type: str,
    payload: CustomAffirmationIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    user_id = str(current_user["_id"])
    doc = await _get_or_create(db, user_id, affirmation_type)
    entry = {"id": str(ObjectId()), "text": payload.text.strip()}
    await db.affirmations.update_one({"_id": doc["_id"]}, {"$push": {"custom": entry}})
    doc.setdefault("custom", []).append(entry)
    daily = await _get_or_generate_daily(db, current_user, affirmation_type)
    return _serialize(doc, affirmation_type, daily)


@router.delete("/{affirmation_type}/custom/{custom_id}", response_model=AffirmationStateOut)
async def delete_custom_affirmation(
    affirmation_type: str,
    custom_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    user_id = str(current_user["_id"])
    doc = await _get_or_create(db, user_id, affirmation_type)
    doc["custom"] = [c for c in doc.get("custom", []) if c["id"] != custom_id]
    await db.affirmations.update_one({"_id": doc["_id"]}, {"$set": {"custom": doc["custom"]}})
    daily = await _get_or_generate_daily(db, current_user, affirmation_type)
    return _serialize(doc, affirmation_type, daily)


@router.put("/{affirmation_type}/journal", response_model=AffirmationStateOut)
async def set_journal_entry(
    affirmation_type: str,
    payload: JournalIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    _validate_type(affirmation_type)
    user_id = str(current_user["_id"])
    doc = await _get_or_create(db, user_id, affirmation_type)
    journal = {"date": date.today().isoformat(), "text": payload.text}
    await db.affirmations.update_one({"_id": doc["_id"]}, {"$set": {"journal": journal}})
    doc["journal"] = journal
    daily = await _get_or_generate_daily(db, current_user, affirmation_type)
    return _serialize(doc, affirmation_type, daily)
