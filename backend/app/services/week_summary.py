from datetime import date, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.day_summary import DaySummaryOut
from app.services.day_summary import get_day_summary


async def get_week_summaries(db: AsyncIOMotorDatabase, user: dict, end_date: date | None = None) -> list[DaySummaryOut]:
    """The last 7 days (oldest first, today last), each built from
    get_day_summary — the same read-mostly aggregation Night Reset uses,
    just repeated. Note that ritual_done/ritual_total is only meaningful for
    today: routines keep a single current-state document, not per-day
    history, so past days always read as 0/0 there until Routines gets real
    history (tracked separately on the roadmap)."""
    end_date = end_date or date.today()
    days = [end_date - timedelta(days=i) for i in range(6, -1, -1)]
    return [await get_day_summary(db, user, d.isoformat()) for d in days]
