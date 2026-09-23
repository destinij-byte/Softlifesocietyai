from datetime import date

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.routers.challenges import TEMPLATES
from app.schemas.day_summary import DaySummaryOut
from app.schemas.weekly_reset import ChallengeWeekOut, GoalOverviewOut, WeeklyResetOut
from app.services.alignment import get_alignment
from app.services.week_summary import get_week_summaries


def _day_composite(d: DaySummaryOut, water_logged: bool) -> float | None:
    """None means "no signal that day," not "zero." water_goal is a fixed
    constant (always > 0) regardless of whether she opened the app, so a
    water ratio only counts when a water_logs document actually exists for
    that date — otherwise every untouched day would trivially "win" at 0%."""
    ratios = []
    if d.ritual_total > 0:
        ratios.append(d.ritual_done / d.ritual_total)
    if water_logged:
        ratios.append(min(1.0, d.water_count / d.water_goal))
    if not ratios:
        return None
    return sum(ratios) / len(ratios)


async def get_weekly_reset(db: AsyncIOMotorDatabase, user: dict) -> WeeklyResetOut:
    """Fully computed from existing collections — no new primary data store.
    Reuses the same day-by-day aggregation Night Reset and Progress/Alignment
    already read, plus a 7-day slice of challenge check-ins and a current
    snapshot of active goals."""
    user_id = str(user["_id"])
    days = await get_week_summaries(db, user)
    week_dates = {d.log_date for d in days}

    water_ratios = [min(1.0, d.water_count / d.water_goal) for d in days if d.water_goal > 0]
    water_avg_pct = round((sum(water_ratios) / len(water_ratios)) * 100, 1) if water_ratios else 0.0
    nourish_days_logged = sum(1 for d in days if d.calories_logged > 0)
    mood_days_logged = sum(1 for d in days if d.mood is not None)

    checkins_completed = await db.daily_checkins.count_documents({"user_id": user_id, "log_date": {"$in": list(week_dates)}})

    water_logged_dates = {
        doc["log_date"]
        for doc in await db.water_logs.find({"user_id": user_id, "log_date": {"$in": list(week_dates)}}).to_list(length=7)
    }

    # A day only wins if it shows genuine positive completion — a 0/8 ritual
    # (the routine merely existing, untouched) shouldn't outrank a day with
    # no signal at all and get crowned "your best day."
    best_day = None
    best_score = 0.0
    for d in days:
        score = _day_composite(d, water_logged=d.log_date in water_logged_dates)
        if score is not None and score > best_score:
            best_score = score
            best_day = date.fromisoformat(d.log_date).strftime("%A")

    participations = await db.challenge_participants.find({"user_id": user_id, "active": True}).to_list(length=50)
    challenges: list[ChallengeWeekOut] = []
    for p in participations:
        template = next((t for t in TEMPLATES if t["slug"] == p["slug"]), None)
        if template is None:
            continue
        check_ins = sum(1 for log_date in p.get("log_dates", []) if log_date in week_dates)
        challenges.append(
            ChallengeWeekOut(slug=p["slug"], title=template["title"], emoji=template["emoji"], check_ins_this_week=check_ins)
        )

    goal_docs = await db.goals.find({"user_id": user_id}).sort("created_at", -1).limit(5).to_list(length=5)
    goals_overview = [GoalOverviewOut(title=g["title"], pillar=g.get("pillar"), progress=g.get("progress", 0)) for g in goal_docs]

    alignment = await get_alignment(db, user)

    return WeeklyResetOut(
        week_start=days[0].log_date,
        week_end=days[-1].log_date,
        days=days,
        water_avg_pct=water_avg_pct,
        nourish_days_logged=nourish_days_logged,
        mood_days_logged=mood_days_logged,
        checkins_completed=checkins_completed,
        best_day=best_day,
        challenges=challenges,
        goals_overview=goals_overview,
        alignment=alignment,
    )
