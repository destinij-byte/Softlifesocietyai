from datetime import date

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/affirmations", tags=["affirmations"])

MORNING_AFFIRMATIONS = [
    "I wake up aligned with the woman I'm becoming.",
    "Today meets me with ease, and I meet it with grace.",
    "I am worthy of the soft, abundant life I'm building.",
    "My energy is a gift — I spend it on what matters.",
    "I trust the timing of my life.",
    "I am the main character of a beautiful story, and today is a good chapter.",
    "Abundance flows to me easily and often.",
    "I choose peace over pressure today.",
    "I am becoming her, one soft morning at a time.",
    "I am safe, I am supported, and I am exactly where I need to be.",
    "My glow is not for anyone else's approval — it's mine.",
    "I move through today with intention, not urgency.",
]

NIGHT_AFFIRMATIONS = [
    "I release today and welcome rest.",
    "I did enough today, and I am enough.",
    "Everything I need is already within me.",
    "I let go of what I can't control and trust what I can.",
    "My rest is productive. My peace is not optional.",
    "I am proud of the woman I'm becoming.",
    "Tomorrow meets a version of me that's already healing.",
    "I forgive myself for anything I'm still holding onto from today.",
    "I close this day with gratitude, not regret.",
    "My dreams are safe with me while I sleep.",
    "I am worthy of softness, even in my own mind.",
    "I trust that what's meant for me is already on its way.",
]

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


class CustomAffirmationIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class CustomAffirmationOut(CustomAffirmationIn):
    id: str


class JournalIn(BaseModel):
    text: str = Field(default="", max_length=2000)


class AffirmationStateOut(BaseModel):
    type: str
    daily_affirmation: str
    manifestation_prompt: str
    custom: list[CustomAffirmationOut] = []
    journal_entry: str = ""


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


def _serialize(doc: dict, affirmation_type: str) -> AffirmationStateOut:
    curated = MORNING_AFFIRMATIONS if affirmation_type == "morning" else NIGHT_AFFIRMATIONS
    today = date.today().isoformat()
    journal = doc.get("journal", {})
    journal_entry = journal.get("text", "") if journal.get("date") == today else ""

    return AffirmationStateOut(
        type=affirmation_type,
        daily_affirmation=_daily_pick(curated),
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
    return _serialize(doc, affirmation_type)


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
    return _serialize(doc, affirmation_type)


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
    return _serialize(doc, affirmation_type)


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
    return _serialize(doc, affirmation_type)
