from datetime import date

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.core.db import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/social", tags=["social"])


class AddFriendRequest(BaseModel):
    email: str


@router.get("/friends")
async def list_friends(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    friend_ids = current_user.get("friend_ids", [])
    if not friend_ids:
        return []

    friends = await db.users.find({"_id": {"$in": [ObjectId(fid) for fid in friend_ids]}}).to_list(length=200)

    today = date.today().isoformat()
    result = []
    for f in friends:
        workout_today = await db.workouts.count_documents(
            {"user_id": str(f["_id"]), "logged_at": {"$gte": _start_of_today()}}
        )
        streak_cursor = db.workouts.find({"user_id": str(f["_id"])}).sort("logged_at", -1)
        recent = await streak_cursor.to_list(length=30)
        result.append(
            {
                "id": str(f["_id"]),
                "name": f["name"],
                "avatar_emoji": f.get("avatar_emoji", "🌸"),
                "moved_today": workout_today > 0,
                "recent_activity_count": len(recent),
            }
        )
    return result


def _start_of_today():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)


@router.post("/friends/add")
async def add_friend(
    payload: AddFriendRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    friend = await db.users.find_one({"email": payload.email.lower()})
    if not friend:
        raise HTTPException(status_code=404, detail="No Soft Life Society member found with that email")
    if str(friend["_id"]) == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="You can't add yourself as a friend")

    await db.users.update_one({"_id": current_user["_id"]}, {"$addToSet": {"friend_ids": str(friend["_id"])}})
    await db.users.update_one({"_id": friend["_id"]}, {"$addToSet": {"friend_ids": str(current_user["_id"])}})
    return {"added": True, "friend_name": friend["name"]}


@router.post("/friends/{friend_id}/encourage")
async def send_encouragement(
    friend_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    friend = await db.users.find_one({"_id": ObjectId(friend_id)})
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")

    await db.encouragements.insert_one(
        {
            "from_user_id": str(current_user["_id"]),
            "from_user_name": current_user["name"],
            "to_user_id": friend_id,
            "message": f"{current_user['name']} is cheering you on! 🎉",
        }
    )
    return {"sent": True}


@router.get("/encouragements")
async def get_encouragements(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.encouragements.find({"to_user_id": str(current_user["_id"])}).sort("_id", -1)
    items = await cursor.to_list(length=50)
    return [{"from_user_name": i["from_user_name"], "message": i["message"]} for i in items]
