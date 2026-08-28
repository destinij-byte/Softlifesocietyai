from datetime import datetime

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user
from app.services.luna import build_message_doc, get_luna_reply

HISTORY_LIMIT = 20

router = APIRouter(prefix="/luna", tags=["luna"])


class ChatMessageIn(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


@router.get("/messages", response_model=list[ChatMessageOut])
async def get_messages(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.luna_messages.find({"user_id": str(current_user["_id"])}).sort("created_at", 1)
    messages = await cursor.to_list(length=200)
    if not messages:
        return [
            ChatMessageOut(
                role="luna",
                content=f"Hola {current_user['name'].split(' ')[0]} 🌸 I'm Luna. I'm here to help you build your soft life, one gentle step at a time. What's on your mind today?",
                created_at=datetime.utcnow(),
            )
        ]
    return [ChatMessageOut(**m) for m in messages]


@router.post("/messages", response_model=ChatMessageOut)
async def send_message(
    payload: ChatMessageIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user_id = str(current_user["_id"])

    history_cursor = db.luna_messages.find({"user_id": user_id}).sort("created_at", -1).limit(HISTORY_LIMIT)
    history = list(reversed(await history_cursor.to_list(length=HISTORY_LIMIT)))

    user_msg = build_message_doc(user_id, "user", payload.message)
    await db.luna_messages.insert_one(user_msg)

    reply_text = await get_luna_reply(payload.message, current_user["name"], history)
    luna_msg = build_message_doc(user_id, "luna", reply_text)
    await db.luna_messages.insert_one(luna_msg)

    return ChatMessageOut(**luna_msg)
