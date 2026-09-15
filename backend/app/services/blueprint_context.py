"""Single source of truth for "what does this user care about right now."

Era and pillar priorities live on the Blueprint document, but nothing should
read that document directly except this service — Luna's context builder,
Home, goal-breakdown generation, and the Night/Weekly Reset aggregators all
go through here so era changes propagate everywhere at once instead of each
feature growing its own era-specific branch.
"""

from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorDatabase

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

    def summary(self) -> str:
        """Short natural-language context for prompting Luna or explaining an
        Alignment score — never a raw data dump."""
        if not self.era and not self.top_pillars and not self.becoming:
            return ""
        parts: list[str] = []
        if self.era_label:
            parts.append(f"She's in her {self.era_label}")
        if self.top_pillars:
            labels = ", ".join(PILLARS[p]["label"] for p in self.top_pillars)
            parts.append(f"currently prioritizing: {labels}")
        if self.becoming:
            parts.append(f'Becoming: "{self.becoming}"')
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

    return BlueprintContext(
        era=era,
        era_label=era_label,
        becoming=doc.get("becoming", "").strip(),
        top_pillars=top_pillars,
    )
