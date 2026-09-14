import asyncio
import random

import anthropic

from app.core.config import get_settings
from app.schemas.nutrition import validate_meal_suggestion
from app.services.ai_client import get_ai_client
from app.services.ai_json import extract_json
from app.services.food_database import foods_fitting_budget

AI_TIMEOUT_SECONDS = 20

ANALYZE_MEAL_PROMPT = """You are a nutrition estimation assistant. Look at this food photo and identify the dish.
Respond with ONLY a JSON object (no markdown, no commentary) in exactly this shape:
{"name": "short dish name", "calories": <int>, "protein_g": <int>, "carbs_g": <int>, "fat_g": <int>, "emoji": "one food emoji", "note": "one short sentence about your estimate, e.g. portion assumptions"}
Estimate for a typical single-serving portion. If you truly cannot identify any food in the image, set "name" to "Unknown food" and all numbers to 0."""

MEAL_BUILDER_PROMPT = """You are Luna Reyes, a soft-life nutrition coach, acting as an AI meal builder. \
Given the user's remaining calories and protein for today, suggest ONE specific, appealing meal that fits. \
Respond with ONLY a JSON object (no markdown, no commentary) in exactly this shape:
{"name": "short meal name", "calories": <int>, "protein_g": <int>, "carbs_g": <int>, "fat_g": <int>, "emoji": "one food emoji", "description": "one warm, encouraging sentence about the meal"}
Stay at or under the remaining calories. Favor protein if remaining protein is high relative to remaining calories. \
Never suggest an unsafely low calorie amount — if remaining calories are very low, suggest a small, sensible \
portion rather than an extreme one, and let the description stay warm and non-restrictive."""


async def analyze_meal_photo(image_b64: str, media_type: str) -> dict | None:
    client = get_ai_client()
    if client is None:
        return None

    settings = get_settings()
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=settings.luna_model,
                max_tokens=400,
                output_config={"effort": "low"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                            {"type": "text", "text": ANALYZE_MEAL_PROMPT},
                        ],
                    }
                ],
            ),
            timeout=AI_TIMEOUT_SECONDS,
        )
    except (anthropic.APIError, asyncio.TimeoutError):
        return None

    if response.stop_reason == "refusal":
        return None

    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        return None
    parsed = extract_json(text)
    if parsed is None:
        return None
    validated = validate_meal_suggestion(parsed)
    return validated.model_dump() if validated else None


async def build_meal_suggestion(remaining_calories: float, remaining_protein: float, meal_type: str) -> dict:
    client = get_ai_client()
    if client is not None:
        settings = get_settings()
        prompt = (
            f"{MEAL_BUILDER_PROMPT}\n\nRemaining today: {remaining_calories:.0f} calories, "
            f"{remaining_protein:.0f}g protein. This meal is for: {meal_type}."
        )
        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model=settings.luna_model,
                    max_tokens=300,
                    output_config={"effort": "low"},
                    messages=[{"role": "user", "content": prompt}],
                ),
                timeout=AI_TIMEOUT_SECONDS,
            )
            if response.stop_reason != "refusal":
                text = next((block.text for block in response.content if block.type == "text"), None)
                parsed = extract_json(text) if text else None
                validated = validate_meal_suggestion(parsed) if parsed else None
                if validated:
                    return validated.model_dump()
        except (anthropic.APIError, asyncio.TimeoutError):
            pass

    candidates = foods_fitting_budget(remaining_calories, remaining_protein)
    if not candidates:
        return {
            "name": "Light snack",
            "calories": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0,
            "emoji": "🍽️",
            "description": "You're right at your goal today — no more food needed, mi amor!",
        }
    pick = random.choice(candidates[:5])
    return {**pick, "description": f"This fits your remaining calories nicely for {meal_type} 💛"}
