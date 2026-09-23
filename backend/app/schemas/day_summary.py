from pydantic import BaseModel


class DaySummaryOut(BaseModel):
    """A read-only snapshot of one day, built from collections that already
    exist (food_logs, water_logs, routines, moods) — Night Reset and, later,
    Weekly Reset both read this instead of each re-deriving their own."""

    log_date: str
    calories_logged: int
    calories_goal: int
    water_count: int
    water_goal: int
    ritual_done: int
    ritual_total: int
    mood: str | None
