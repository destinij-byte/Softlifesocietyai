"""Single source of truth for "what does this user care about right now."

Era and pillar priorities live on the Blueprint document, but nothing should
read that document directly except this service — Luna's context builder,
Home, goal-breakdown generation, and the Night/Weekly Reset aggregators all
go through here so era changes propagate everywhere at once instead of each
feature growing its own era-specific branch.
"""

from dataclasses import dataclass, field

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.personalization import COACHING_STYLES, MOTIVATION_STYLES
from app.schemas.pillars import ERAS, PILLARS

# How many top-weighted pillars count as "current priorities" for ranking
# purposes elsewhere (Luna suggestions, Home tile order, breakdown emphasis).
TOP_PILLAR_COUNT = 3


@dataclass
class BlueprintContext:
    era: str | None
    era_label: str | None
    becoming: str
    top_pillars: list[str]  # pillar keys, ranked by priority weight desc

    # Personalization — how Luna should talk to her and what actually moves
    # her to act. None means "not set," not "use a default style silently";
    # callers decide whether to fall back to the base voice.
    preferred_name: str | None = None
    coaching_style: str | None = None
    motivation_style: str | None = None
    affirmation_categories: list[str] = field(default_factory=list)
    manifestation_categories: list[str] = field(default_factory=list)
    dietary_style: str | None = None

    def summary(self) -> str:
        """Short natural-language context for prompting Luna or explaining an
        Alignment score — never a raw data dump."""
        if not any(
            [self.era, self.top_pillars, self.becoming, self.coaching_style, self.motivation_style, self.preferred_name]
        ):
            return ""
        parts: list[str] = []
        if self.preferred_name:
            parts.append(f"She goes by {self.preferred_name}")
        if self.era_label:
            parts.append(f"She's in her {self.era_label}")
        if self.top_pillars:
            labels = ", ".join(PILLARS[p]["label"] for p in self.top_pillars)
            parts.append(f"currently prioritizing: {labels}")
        if self.becoming:
            parts.append(f'Becoming: "{self.becoming}"')
        if self.coaching_style:
            parts.append(f"Preferred coaching style: {COACHING_STYLES[self.coaching_style]['label']}")
        if self.motivation_style:
            parts.append(f"What motivates her: {MOTIVATION_STYLES[self.motivation_style]['label']}")
        return ". ".join(parts) + "."

    def pillar_rank(self, pillar: str | None) -> int:
        """Lower = higher priority. A pillar outside her top priorities (or
        None) sorts after every ranked pillar, not before — so unweighted
        content never jumps the queue just because it's unranked."""
        if pillar is not None and pillar in self.top_pillars:
            return self.top_pillars.index(pillar)
        return len(self.top_pillars)


EMPTY_CONTEXT = BlueprintContext(era=None, era_label=None, becoming="", top_pillars=[])


async def get_blueprint_context(db: AsyncIOMotorDatabase, user_id: str) -> BlueprintContext:
    doc = await db.blueprints.find_one({"user_id": user_id})
    if doc is None:
        return EMPTY_CONTEXT

    era = doc.get("era")
    era_label = ERAS[era]["label"] if era in ERAS else None

    pillars = sorted(doc.get("pillars", []), key=lambda p: p.get("priority", 0), reverse=True)
    top_pillars = [p["pillar"] for p in pillars[:TOP_PILLAR_COUNT] if p.get("pillar") in PILLARS]

    coaching_style = doc.get("coaching_style")
    motivation_style = doc.get("motivation_style")
    nutrition_preferences = doc.get("nutrition_preferences") or {}

    return BlueprintContext(
        era=era,
        era_label=era_label,
        becoming=doc.get("becoming", "").strip(),
        top_pillars=top_pillars,
        preferred_name=doc.get("preferred_name"),
        coaching_style=coaching_style if coaching_style in COACHING_STYLES else None,
        motivation_style=motivation_style if motivation_style in MOTIVATION_STYLES else None,
        affirmation_categories=doc.get("affirmation_categories", []),
        manifestation_categories=doc.get("manifestation_categories", []),
        dietary_style=nutrition_preferences.get("dietary_style"),
    )
