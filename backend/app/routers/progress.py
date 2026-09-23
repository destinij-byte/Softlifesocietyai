from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.deps import get_current_user
from app.schemas.progress import AlignmentOut
from app.services.alignment import get_alignment

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/alignment", response_model=AlignmentOut)
async def get_alignment_score(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await get_alignment(db, current_user)
