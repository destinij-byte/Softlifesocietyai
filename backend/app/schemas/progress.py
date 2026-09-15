from pydantic import BaseModel


class PillarAlignment(BaseModel):
    pillar: str
    label: str
    score: float  # 0..1


class AlignmentOut(BaseModel):
    """Never a bare percentage — score always ships with why, naming which
    pillars pulled it up or down this week."""

    score: float  # 0..1
    why: str
    pillar_scores: list[PillarAlignment]
