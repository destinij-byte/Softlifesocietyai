import secrets

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/social", tags=["social"])


class RedeemInviteRequest(BaseModel):
    code: str


async def _ensure_invite_code(db: AsyncIOMotorDatabase, user: dict) -> str:
    code = user.get("invite_code")
    if code:
        return code
    code = secrets.token_hex(4)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"invite_code": code}})
    return code


@router.get("/invite-code")
async def get_invite_code(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    code = await _ensure_invite_code(db, current_user)
    return {"code": code, "invite_link": f"softlifesociety://invite/{code}"}


@router.post("/invite/redeem")
async def redeem_invite(
    payload: RedeemInviteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    inviter = await db.users.find_one({"invite_code": payload.code})
    if not inviter:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    if str(inviter["_id"]) == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="You can't invite yourself")

    await db.users.update_one({"_id": current_user["_id"]}, {"$addToSet": {"friend_ids": str(inviter["_id"])}})
    await db.users.update_one({"_id": inviter["_id"]}, {"$addToSet": {"friend_ids": str(current_user["_id"])}})
    return {"joined": True, "friend_name": inviter["name"]}


@router.get("/friends")
async def list_friends(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    friend_ids = current_user.get("friend_ids", [])
    if not friend_ids:
        return []
    friends = await db.users.find({"_id": {"$in": [ObjectId(fid) for fid in friend_ids]}}).to_list(length=200)
    return [{"id": str(f["_id"]), "name": f["name"], "avatar_emoji": f.get("avatar_emoji", "🌸")} for f in friends]
