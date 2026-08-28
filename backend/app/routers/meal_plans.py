from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.services.meal_plans import get_meal_plan, get_meal_plans

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


@router.get("")
async def list_plans():
    return get_meal_plans()


@router.get("/active")
async def get_active_plan(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    active_id = current_user.get("active_meal_plan_id")
    if not active_id:
        return {"active_plan": None}
    return {"active_plan": get_meal_plan(active_id)}


@router.post("/{plan_id}/activate")
async def activate_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    plan = get_meal_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"active_meal_plan_id": plan_id}})
    return {"active_plan": plan}
