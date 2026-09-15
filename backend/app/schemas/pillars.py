"""Shared vocabulary for the Personal Life Blueprint — the eight areas the
Become Her system reasons about, and the "eras" a user can be in. Both goals
and the Blueprint reference these so a goal's pillar and a Blueprint's
priorities are always talking about the same eight things."""

PILLARS = {
    "mind": {"label": "Mind", "emoji": "🧠"},
    "body": {"label": "Body", "emoji": "🌿"},
    "glow": {"label": "Glow", "emoji": "✨"},
    "money": {"label": "Money", "emoji": "💰"},
    "career": {"label": "Career", "emoji": "💼"},
    "home": {"label": "Home", "emoji": "🏡"},
    "relationships": {"label": "Relationships", "emoji": "💛"},
    "growth": {"label": "Growth", "emoji": "🌱"},
}

ERAS = {
    "glow_up": {"label": "Glow-Up Era", "emoji": "✨"},
    "wellness": {"label": "Wellness Era", "emoji": "🌿"},
    "money": {"label": "Money Era", "emoji": "💰"},
    "ceo": {"label": "CEO Era", "emoji": "💼"},
    "discipline": {"label": "Discipline Era", "emoji": "🎯"},
    "peace": {"label": "Peace Era", "emoji": "🕊️"},
    "new": {"label": "New Era", "emoji": "🌅"},
    "soft_life": {"label": "Soft Life Era", "emoji": "🤍"},
}


def is_valid_pillar(pillar: str) -> bool:
    return pillar in PILLARS


def is_valid_era(era: str) -> bool:
    return era in ERAS
