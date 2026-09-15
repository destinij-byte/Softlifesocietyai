from datetime import datetime

from pydantic import BaseModel, Field, ValidationError, field_validator

# The only actions Luna is ever allowed to suggest. Adding a new one here is
# a deliberate decision — the backend must already have a real, authorized
# endpoint behind it before it's added; the model can never execute anything
# on its own, only propose a button the user taps (which then calls that
# existing, already-authorized endpoint, e.g. POST /goals).
ACTION_ALLOWLIST = {"create_goal", "generate_breakdown"}


class LunaAction(BaseModel):
    type: str
    label: str = Field(min_length=1, max_length=60)
    payload: dict = Field(default_factory=dict)


class BreakdownStepPayload(BaseModel):
    period: str
    label: str = Field(min_length=1, max_length=200)
    target: float | None = None

    @field_validator("period")
    @classmethod
    def _check_period(cls, value: str) -> str:
        if value not in ("monthly", "weekly", "today"):
            raise ValueError("period must be monthly, weekly, or today")
        return value


class GenerateBreakdownPayload(BaseModel):
    """generate_breakdown extends the existing goals breakdown CRUD
    (POST /goals/{id}/breakdown) — Luna proposes steps, the frontend resolves
    goal_title to an id the user already owns, and nothing saves until the
    user taps the button."""

    goal_title: str = Field(min_length=1, max_length=160)
    steps: list[BreakdownStepPayload] = Field(min_length=1, max_length=12)


# Action types whose payload shape needs stricter validation than "any dict"
# before the button is ever shown to the user.
ACTION_PAYLOAD_VALIDATORS: dict[str, type[BaseModel]] = {
    "generate_breakdown": GenerateBreakdownPayload,
}


def validate_actions(raw_actions: object) -> list[LunaAction]:
    """Never trust model output: silently drop anything malformed or outside
    the allowlist rather than surfacing a broken action button."""
    if not isinstance(raw_actions, list):
        return []
    validated: list[LunaAction] = []
    for item in raw_actions:
        if not isinstance(item, dict) or item.get("type") not in ACTION_ALLOWLIST:
            continue
        try:
            action = LunaAction(**item)
        except ValidationError:
            continue

        payload_model = ACTION_PAYLOAD_VALIDATORS.get(action.type)
        if payload_model is not None:
            try:
                payload_model(**action.payload)
            except ValidationError:
                continue

        validated.append(action)
    return validated


class ChatMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    mode: str = "life"


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    mode: str = "life"
    actions: list[LunaAction] = []
    created_at: datetime


class MemoryIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class MemoryOut(BaseModel):
    id: str
    text: str
    created_at: datetime
