from pydantic import BaseModel, Field, ValidationError


class MealSuggestionOut(BaseModel):
    """Shape every AI-generated meal (photo analysis or meal-builder) must
    satisfy before it ever reaches a router or the client. Numeric fields are
    bounded so a hallucinated or malformed model response can't produce an
    unsafe or nonsensical suggestion (e.g. negative calories, a 50,000-calorie
    "snack")."""

    name: str = Field(min_length=1, max_length=120)
    calories: int = Field(ge=0, le=5000)
    protein_g: float = Field(ge=0, le=500)
    carbs_g: float = Field(ge=0, le=500)
    fat_g: float = Field(ge=0, le=500)
    emoji: str = Field(default="🍽️", max_length=8)
    description: str | None = Field(default=None, max_length=280)
    note: str | None = Field(default=None, max_length=280)


def validate_meal_suggestion(data: dict) -> MealSuggestionOut | None:
    """Never trust model output: validate it here, before it reaches a
    router. Returns None on failure so callers can fall back to a templated
    or locally-computed suggestion instead of surfacing a raw error."""
    try:
        return MealSuggestionOut(**data)
    except (ValidationError, TypeError):
        return None
