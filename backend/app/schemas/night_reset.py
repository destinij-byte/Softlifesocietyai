from pydantic import BaseModel, Field

from app.schemas.day_summary import DaySummaryOut


class NightCheckinIn(BaseModel):
    win: str = Field(default="", max_length=300)
    gratitude: str = Field(default="", max_length=300)
    tomorrow_focus: str = Field(default="", max_length=200)


class NightCheckinOut(NightCheckinIn):
    log_date: str
    completed: bool
    day_summary: DaySummaryOut
