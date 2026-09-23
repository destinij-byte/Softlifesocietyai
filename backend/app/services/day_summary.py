from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.day_summary import DaySummaryOut

# Mirrors nutrition.py's DEFAULT_GOALS/WATER_GOAL_GLASSES — duplicated rather
# than imported to avoid a circular import (nutrition.py doesn't need this
# module), but the values must stay in sync with app/routers/nutrition.py.
DEFAULT_CALORIE_GOAL = 1650
WATER_GOAL_GLASSES = 8


async def get_day_summary(db: AsyncIOMotorDatabase, user: dict, log_date: str) -> DaySummaryOut:
    user_id = str(user["_id"])

    food_entries = await db.food_logs.find({"user_id": user_id, "log_date": log_date}).to_list(length=200)
    calories_logged = sum(e.get("calories", 0) for e in food_entries)

    water_doc = await db.water_logs.find_one({"user_id": user_id, "log_date": log_date})
    water_count = water_doc["count"] if water_doc else 0

    ritual_done = 0
    ritual_total = 0
    routines = await db.routines.find({"user_id": user_id}).to_list(length=10)
    for routine in routines:
        # A routine only counts toward this day's ritual if it was actually
        # reset for this day — an untouched routine from a prior day isn't
        # "today's ritual."
        if routine.get("reset_date") != log_date:
            continue
        steps = routine.get("steps", [])
        ritual_total += len(steps)
        ritual_done += sum(1 for s in steps if s.get("done"))

    mood_doc = await db.moods.find_one({"user_id": user_id, "log_date": log_date})

    return DaySummaryOut(
        log_date=log_date,
        calories_logged=calories_logged,
        calories_goal=user.get("calorie_goal", DEFAULT_CALORIE_GOAL),
        water_count=water_count,
        water_goal=WATER_GOAL_GLASSES,
        ritual_done=ritual_done,
        ritual_total=ritual_total,
        mood=mood_doc["mood"] if mood_doc else None,
    )
