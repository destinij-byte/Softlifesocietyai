from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user
from app.services.luna import MODE_PROMPTS, build_message_doc, get_luna_reply

router = APIRouter(prefix="/luna", tags=["luna"])

HISTORY_LIMIT = 20
MODES = tuple(MODE_PROMPTS.keys())

MODE_GREETINGS = {
    "life": "Hola {name} 🌸 I'm Luna. I'm here to help you build your soft life, one gentle step at a time. What's on your mind today?",
    "money": "Hey {name} 💰 let's talk money — budgeting, saving, whatever's on your mind, no judgment here.",
    "wellness": "Hi {name} 🍓 I can see your nutrition and movement — want help planning your day around it?",
    "goals": "{name} 🎯 let's turn your goals into small, doable steps. What are you working toward?",
}


class ChatMessageIn(BaseModel):
    message: str
    mode: str = "life"


class ChatMessageOut(BaseModel):
    role: str
    content: str
    mode: str = "life"
    created_at: datetime


def _validate_mode(mode: str) -> str:
    return mode if mode in MODES else "life"


async def _build_context_summary(db: AsyncIOMotorDatabase, user_id: str, mode: str) -> str:
    parts: list[str] = []

    if mode in ("wellness", "life"):
        today = date.today().isoformat()
        entries = await db.food_logs.find({"user_id": user_id, "log_date": today}).to_list(length=50)
        total_cal = sum(e["calories"] for e in entries)
        parts.append(f"Logged {total_cal} calories so far today across {len(entries)} entries.")

    if mode in ("goals", "life"):
        goals = await db.goals.find({"user_id": user_id}).sort("created_at", -1).limit(5).to_list(length=5)
        if goals:
            goal_lines = ", ".join(f"{g['title']} ({int(g.get('progress', 0) * 100)}% done)" for g in goals)
            parts.append(f"Active goals: {goal_lines}.")

    return " ".join(parts)


@router.get("/messages", response_model=list[ChatMessageOut])
async def get_messages(
    mode: str = Query("life"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    mode = _validate_mode(mode)
    cursor = db.luna_messages.find({"user_id": str(current_user["_id"]), "mode": mode}).sort("created_at", 1)
    messages = await cursor.to_list(length=200)
    if not messages:
        greeting = MODE_GREETINGS[mode].format(name=current_user["name"].split(" ")[0])
        return [ChatMessageOut(role="luna", content=greeting, mode=mode, created_at=datetime.utcnow())]
    return [ChatMessageOut(**m) for m in messages]


@router.post("/messages", response_model=ChatMessageOut)
async def send_message(
    payload: ChatMessageIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    mode = _validate_mode(payload.mode)
    user_id = str(current_user["_id"])

    history_cursor = db.luna_messages.find({"user_id": user_id, "mode": mode}).sort("created_at", -1).limit(HISTORY_LIMIT)
    history = list(reversed(await history_cursor.to_list(length=HISTORY_LIMIT)))

    context_summary = await _build_context_summary(db, user_id, mode)

    user_msg = build_message_doc(user_id, "user", payload.message, mode)
    await db.luna_messages.insert_one(user_msg)

    reply_text = await get_luna_reply(payload.message, current_user["name"], history, mode, context_summary)
    luna_msg = build_message_doc(user_id, "luna", reply_text, mode)
    await db.luna_messages.insert_one(luna_msg)

    return ChatMessageOut(**luna_msg)
