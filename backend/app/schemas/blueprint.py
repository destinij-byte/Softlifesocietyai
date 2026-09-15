from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.pillars import ERAS, PILLARS


class PillarPriority(BaseModel):
    pillar: str
    priority: int = Field(ge=1, le=5)

    @field_validator("pillar")
    @classmethod
    def _check_pillar(cls, value: str) -> str:
        if value not in PILLARS:
            raise ValueError("Unknown pillar")
        return value


class BlueprintIn(BaseModel):
    era: str | None = None
    current_state: str = Field(default="", max_length=600)
    becoming: str = Field(default="", max_length=600)
    pillars: list[PillarPriority] = Field(default_factory=list)

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


class BlueprintOut(BlueprintIn):
    created_at: datetime
    updated_at: datetime
