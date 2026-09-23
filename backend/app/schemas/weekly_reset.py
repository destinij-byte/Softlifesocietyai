from pydantic import BaseModel

from app.schemas.day_summary import DaySummaryOut
from app.schemas.progress import AlignmentOut


class ChallengeWeekOut(BaseModel):
    slug: str
    title: str
    emoji: str
    check_ins_this_week: int


class GoalOverviewOut(BaseModel):
    title: str
    pillar: str | None
    progress: float


class WeeklyResetOut(BaseModel):
    week_start: str
    week_end: str
    days: list[DaySummaryOut]
    water_avg_pct: float
    nourish_days_logged: int
    mood_days_logged: int
    checkins_completed: int
    best_day: str | None
    challenges: list[ChallengeWeekOut]
    goals_overview: list[GoalOverviewOut]
    alignment: AlignmentOut
