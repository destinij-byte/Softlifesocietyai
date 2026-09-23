from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.pillars import ERAS, PILLARS
from app.schemas.personalization import (
    AFFIRMATION_CATEGORIES,
    DIETARY_STYLES,
    MANIFESTATION_CATEGORIES,
    MOTIVATION_STYLES,
    COACHING_STYLES,
)


class PillarPriority(BaseModel):
    pillar: str
    priority: int = Field(ge=1, le=5)

    @field_validator("pillar")
    @classmethod
    def _check_pillar(cls, value: str) -> str:
        if value not in PILLARS:
            raise ValueError("Unknown pillar")
        return value


class NutritionPreferences(BaseModel):
    dietary_style: str | None = None
    notes: str = Field(default="", max_length=300)

    @field_validator("dietary_style")
    @classmethod
    def _check_dietary_style(cls, value: str | None) -> str | None:
        if value is not None and value not in DIETARY_STYLES:
            raise ValueError("Unknown dietary style")
        return value


class BlueprintIn(BaseModel):
    era: str | None = None
    current_state: str = Field(default="", max_length=600)
    becoming: str = Field(default="", max_length=600)
    pillars: list[PillarPriority] = Field(default_factory=list)

    # Personalization — how Luna talks to her, what motivates her, and her
    # default category/dietary preferences. All optional and additive: an
    # existing Blueprint document with none of these set just reads as None
    # / empty everywhere they're consumed.
    preferred_name: str | None = Field(default=None, max_length=60)
    coaching_style: str | None = None
    motivation_style: str | None = None
    affirmation_categories: list[str] = Field(default_factory=list)
    manifestation_categories: list[str] = Field(default_factory=list)
    nutrition_preferences: NutritionPreferences = Field(default_factory=NutritionPreferences)

    @field_validator("era")
    @classmethod
    def _check_era(cls, value: str | None) -> str | None:
        if value is not None and value not in ERAS:
            raise ValueError("Unknown era")
        return value

    @field_validator("pillars")
    @classmethod
    def _check_unique_pillars(cls, value: list[PillarPriority]) -> list[PillarPriority]:
        seen = {p.pillar for p in value}
        if len(seen) != len(value):
            raise ValueError("Each pillar may only appear once")
        return value

    @field_validator("coaching_style")
    @classmethod
    def _check_coaching_style(cls, value: str | None) -> str | None:
        if value is not None and value not in COACHING_STYLES:
            raise ValueError("Unknown coaching style")
        return value

    @field_validator("motivation_style")
    @classmethod
    def _check_motivation_style(cls, value: str | None) -> str | None:
        if value is not None and value not in MOTIVATION_STYLES:
            raise ValueError("Unknown motivation style")
        return value

    @field_validator("affirmation_categories")
    @classmethod
    def _check_affirmation_categories(cls, value: list[str]) -> list[str]:
        if any(v not in AFFIRMATION_CATEGORIES for v in value):
            raise ValueError("Unknown affirmation category")
        return value

    @field_validator("manifestation_categories")
    @classmethod
    def _check_manifestation_categories(cls, value: list[str]) -> list[str]:
        if any(v not in MANIFESTATION_CATEGORIES for v in value):
            raise ValueError("Unknown manifestation category")
        return value


class BlueprintOut(BlueprintIn):
    created_at: datetime
    updated_at: datetime
