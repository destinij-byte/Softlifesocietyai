from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.pillars import PILLARS
from app.schemas.progress import AlignmentOut, PillarAlignment
from app.services.blueprint_context import get_blueprint_context
from app.services.week_summary import get_week_summaries


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


async def get_alignment(db: AsyncIOMotorDatabase, user: dict) -> AlignmentOut:
    """A computed, never-stored score: how much of this week's activity
    lines up with her Blueprint's current priorities. Built entirely from
    existing collections (day summaries + goals + the Blueprint) — nothing
    here is a new primary data store, per the architecture plan."""
    user_id = str(user["_id"])
    days = await get_week_summaries(db, user)

    water_scores = [_clamp(d.water_count / d.water_goal) for d in days if d.water_goal > 0]
    water_avg = sum(water_scores) / len(water_scores) if water_scores else None
    nourish_avg = sum(1 for d in days if d.calories_logged > 0) / len(days)
    mood_avg = sum(1 for d in days if d.mood is not None) / len(days)

    checkin_count = await db.daily_checkins.count_documents({"user_id": user_id, "log_date": {"$in": [d.log_date for d in days]}})
    checkin_avg = checkin_count / len(days)

    pillar_signals: dict[str, list[float]] = {"body": [nourish_avg], "mind": [checkin_avg, mood_avg]}
    if water_avg is not None:
        pillar_signals["body"].append(water_avg)

    goals = await db.goals.find({"user_id": user_id}).to_list(length=200)
    goal_pillar_progress: dict[str, list[float]] = {}
    for g in goals:
        pillar = g.get("pillar")
        if pillar in PILLARS:
            goal_pillar_progress.setdefault(pillar, []).append(g.get("progress", 0))
    for pillar, values in goal_pillar_progress.items():
        pillar_signals.setdefault(pillar, []).append(sum(values) / len(values))

    averaged = {pillar: sum(values) / len(values) for pillar, values in pillar_signals.items() if values}

    ctx = await get_blueprint_context(db, user_id)
    considered_pillars = [p for p in ctx.top_pillars if p in averaged] or list(averaged.keys())
    considered = {p: averaged[p] for p in considered_pillars}

    overall = sum(considered.values()) / len(considered) if considered else 0.0

    if considered:
        best = max(considered, key=considered.get)
        worst = min(considered, key=considered.get)
        if best == worst:
            why = f"{PILLARS[best]['label']} is carrying this week."
        else:
            why = f"{PILLARS[best]['label']} led the way this week, while {PILLARS[worst]['label']} had the least movement."
    else:
        why = "Log a few days of activity and Luna will start showing you what's driving your Alignment."

    pillar_scores = [
        PillarAlignment(pillar=p, label=PILLARS[p]["label"], score=round(s, 2))
        for p, s in sorted(averaged.items(), key=lambda kv: -kv[1])
    ]

    return AlignmentOut(score=round(overall, 2), why=why, pillar_scores=pillar_scores)
