from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.weekly_reset import WeeklyResetOut
from app.services.weekly_reset import get_weekly_reset

router = APIRouter(prefix="/weekly-reset", tags=["weekly-reset"])


@router.get("/summary", response_model=WeeklyResetOut)
async def get_weekly_reset_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_weekly_reset(db, current_user)
