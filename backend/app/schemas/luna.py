from datetime import datetime

from pydantic import BaseModel, Field, ValidationError

# The only actions Luna is ever allowed to suggest. Adding a new one here is
# a deliberate decision — the backend must already have a real, authorized
# endpoint behind it before it's added; the model can never execute anything
# on its own, only propose a button the user taps (which then calls that
# existing, already-authorized endpoint, e.g. POST /goals).
ACTION_ALLOWLIST = {"create_goal"}


class LunaAction(BaseModel):
    type: str
    label: str = Field(min_length=1, max_length=60)
    payload: dict = Field(default_factory=dict)


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
            validated.append(LunaAction(**item))
        except ValidationError:
            continue
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
