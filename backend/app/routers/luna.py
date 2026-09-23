from datetime import date, datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import check_rate_limit
from app.schemas.luna import ChatMessageIn, ChatMessageOut, MemoryIn, MemoryOut
from app.services.blueprint_context import get_blueprint_context
from app.services.luna import MODE_PROMPTS, build_message_doc, get_luna_reply

router = APIRouter(prefix="/luna", tags=["luna"])

# How many raw prior messages get sent to the model on every call — kept
# small on purpose (see cost-control note in send_message below).
AI_HISTORY_RAW_LIMIT = 10
DISPLAY_HISTORY_LIMIT = 200
MODES = tuple(MODE_PROMPTS.keys())

MAX_MEMORIES = 20

# Simple per-user rate limit so one runaway client (or a scripted abuse case)
# can't drive unbounded Anthropic spend. A real product would tier this by
# subscription plan (see Phase 3 entitlements) — flat limit for now.
LUNA_MESSAGE_LIMIT_PER_HOUR = 40

MODE_GREETINGS = {
    "life": "Hola {name} 🌸 I'm Luna. I'm here to help you build your soft life, one gentle step at a time. What's on your mind today?",
    "money": "Hey {name} 💰 let's talk money — budgeting, saving, whatever's on your mind, no judgment here.",
    "wellness": "Hi {name} 🍓 I can see your nutrition and movement — want help planning your day around it?",
    "goals": "{name} 🎯 let's turn your goals into small, doable steps. What are you working toward?",
}


def _validate_mode(mode: str) -> str:
    return mode if mode in MODES else "life"


async def _check_luna_rate_limit(db: AsyncIOMotorDatabase, user_id: str) -> None:
    await check_rate_limit(
        db,
        f"luna:{user_id}",
        LUNA_MESSAGE_LIMIT_PER_HOUR,
        timedelta(hours=1),
        "You've reached Luna's hourly message limit — she'll be ready again soon.",
    )


async def _build_context_summary(db: AsyncIOMotorDatabase, user_id: str, mode: str) -> str:
    """Structured, mode-gated context — only what's relevant to the current
    question, never a dump of every collection the user owns."""
    parts: list[str] = []

    # Era/pillar priorities are relevant to every mode — this is what makes
    # Luna's suggestions era-aware without a mode-specific branch for it.
    blueprint = await get_blueprint_context(db, user_id)
    blueprint_summary = blueprint.summary()
    if blueprint_summary:
        parts.append(blueprint_summary)

    if mode in ("wellness", "life"):
        today = date.today().isoformat()
        entries = await db.food_logs.find({"user_id": user_id, "log_date": today}).to_list(length=50)
        total_cal = sum(e["calories"] for e in entries)
        water = await db.water_logs.find_one({"user_id": user_id, "log_date": today})
        parts.append(
            f"Logged {total_cal} calories so far today across {len(entries)} entries; "
            f"{(water or {}).get('count', 0)} glasses of water."
        )

    if mode in ("wellness", "life"):
        routine = await db.routines.find_one({"user_id": user_id, "type": "morning"})
        if routine and routine.get("steps"):
            done = sum(1 for s in routine["steps"] if s.get("done"))
            parts.append(f"Morning routine: {done}/{len(routine['steps'])} steps done today.")

    if mode in ("goals", "life"):
        goals = await db.goals.find({"user_id": user_id}).sort("created_at", -1).limit(3).to_list(length=3)
        if goals:
            goal_lines = ", ".join(f"{g['title']} ({int(g.get('progress', 0) * 100)}% done)" for g in goals)
            parts.append(f"Active goals: {goal_lines}.")

    memories = await db.luna_memories.find({"user_id": user_id}).sort("created_at", -1).limit(5).to_list(length=5)
    if memories:
        parts.append("Things she's asked you to remember: " + "; ".join(m["text"] for m in memories) + ".")

    return " ".join(parts)


@router.get("/messages", response_model=list[ChatMessageOut])
async def get_messages(
    mode: str = Query("life"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    mode = _validate_mode(mode)
    cursor = db.luna_messages.find({"user_id": str(current_user["_id"]), "mode": mode}).sort("created_at", 1)
    messages = await cursor.to_list(length=DISPLAY_HISTORY_LIMIT)
    if not messages:
        greeting = MODE_GREETINGS[mode].format(name=current_user["name"].split(" ")[0])
        return [ChatMessageOut(id="greeting", role="luna", content=greeting, mode=mode, actions=[], created_at=datetime.utcnow())]
    return [ChatMessageOut(id=str(m["_id"]), role=m["role"], content=m["content"], mode=m.get("mode", "life"), actions=m.get("actions", []), created_at=m["created_at"]) for m in messages]


@router.post("/messages", response_model=ChatMessageOut)
async def send_message(
    payload: ChatMessageIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    mode = _validate_mode(payload.mode)
    user_id = str(current_user["_id"])

    await _check_luna_rate_limit(db, user_id)

    # Cost control: only the last AI_HISTORY_RAW_LIMIT messages are ever sent
    # to the model — never the full conversation history, no matter how long
    # the thread has run.
    history_cursor = db.luna_messages.find({"user_id": user_id, "mode": mode}).sort("created_at", -1).limit(AI_HISTORY_RAW_LIMIT)
    history = list(reversed(await history_cursor.to_list(length=AI_HISTORY_RAW_LIMIT)))

    context_summary = await _build_context_summary(db, user_id, mode)

    user_msg = build_message_doc(user_id, "user", payload.message, mode)
    await db.luna_messages.insert_one(user_msg)

    reply_text, actions = await get_luna_reply(payload.message, current_user["name"], history, mode, context_summary)
    luna_msg = build_message_doc(user_id, "luna", reply_text, mode, actions)
    result = await db.luna_messages.insert_one(luna_msg)
    luna_msg["_id"] = result.inserted_id

    return ChatMessageOut(id=str(luna_msg["_id"]), role="luna", content=reply_text, mode=mode, actions=actions, created_at=luna_msg["created_at"])


@router.get("/memory", response_model=list[MemoryOut])
async def list_memories(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.luna_memories.find({"user_id": str(current_user["_id"])}).sort("created_at", -1)
    memories = await cursor.to_list(length=MAX_MEMORIES)
    return [MemoryOut(id=str(m["_id"]), text=m["text"], created_at=m["created_at"]) for m in memories]


@router.post("/memory", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
async def add_memory(
    payload: MemoryIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user_id = str(current_user["_id"])
    count = await db.luna_memories.count_documents({"user_id": user_id})
    if count >= MAX_MEMORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Luna can only hold {MAX_MEMORIES} memories at once — remove one to add another.",
        )
    doc = {"user_id": user_id, "text": payload.text.strip(), "created_at": datetime.now(timezone.utc)}
    result = await db.luna_memories.insert_one(doc)
    return MemoryOut(id=str(result.inserted_id), text=doc["text"], created_at=doc["created_at"])


@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        object_id = ObjectId(memory_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid memory id")
    await db.luna_memories.delete_one({"_id": object_id, "user_id": str(current_user["_id"])})
    return None
