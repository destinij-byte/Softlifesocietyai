"""Shared vocabulary for the PersonalBlueprint's personalization fields —
how Luna should talk to her (coaching_style), what actually moves her to
act (motivation_style), and which affirmation/manifestation categories and
dietary style she cares about. Same {key: {label, emoji}} catalog pattern
as app/schemas/pillars.py, for the same reason: the frontend renders these
without hardcoding copy, and the backend validates against the same source
of truth."""

COACHING_STYLES = {
    "gentle": {"label": "Gentle & nurturing", "emoji": "🤍"},
    "direct": {"label": "Direct & no-fluff", "emoji": "🎯"},
    "tough_love": {"label": "Tough love", "emoji": "🔥"},
    "cheerleader": {"label": "Hype & celebratory", "emoji": "🎉"},
}

MOTIVATION_STYLES = {
    "accountability": {"label": "Accountability & structure", "emoji": "📋"},
    "encouragement": {"label": "Encouragement & softness", "emoji": "🌸"},
    "results": {"label": "Data & results", "emoji": "📈"},
    "big_picture": {"label": "Big picture & meaning", "emoji": "🌅"},
}

AFFIRMATION_CATEGORIES = {
    "self_worth": {"label": "Self-worth", "emoji": "💛"},
    "confidence": {"label": "Confidence", "emoji": "✨"},
    "money": {"label": "Money", "emoji": "💰"},
    "career": {"label": "Career", "emoji": "💼"},
    "business": {"label": "Business", "emoji": "📊"},
    "discipline": {"label": "Discipline", "emoji": "🎯"},
    "wellness": {"label": "Wellness", "emoji": "🌿"},
    "peace": {"label": "Peace", "emoji": "🕊️"},
    "relationships": {"label": "Relationships", "emoji": "💞"},
    "personal_growth": {"label": "Personal growth", "emoji": "🌱"},
    "transformation": {"label": "Transformation", "emoji": "🦋"},
}

MANIFESTATION_CATEGORIES = {
    "financial_freedom": {"label": "Financial freedom", "emoji": "💰"},
    "dream_home": {"label": "Dream home", "emoji": "🏡"},
    "career": {"label": "Career", "emoji": "💼"},
    "business": {"label": "Business", "emoji": "📊"},
    "confidence": {"label": "Confidence", "emoji": "✨"},
    "relationships": {"label": "Relationships", "emoji": "💞"},
    "health_wellness": {"label": "Health & wellness", "emoji": "🌿"},
    "peace": {"label": "Peace", "emoji": "🕊️"},
    "travel": {"label": "Travel", "emoji": "✈️"},
    "personal_growth": {"label": "Personal growth", "emoji": "🌱"},
}

DIETARY_STYLES = {
    "none": {"label": "No specific style", "emoji": "🍽️"},
    "vegetarian": {"label": "Vegetarian", "emoji": "🥦"},
    "vegan": {"label": "Vegan", "emoji": "🌱"},
    "pescatarian": {"label": "Pescatarian", "emoji": "🐟"},
    "gluten_free": {"label": "Gluten-free", "emoji": "🌾"},
    "dairy_free": {"label": "Dairy-free", "emoji": "🥛"},
    "low_carb": {"label": "Low-carb", "emoji": "🥑"},
}


def is_valid_coaching_style(value: str) -> bool:
    return value in COACHING_STYLES


def is_valid_motivation_style(value: str) -> bool:
    return value in MOTIVATION_STYLES


def is_valid_affirmation_category(value: str) -> bool:
    return value in AFFIRMATION_CATEGORIES


def is_valid_manifestation_category(value: str) -> bool:
    return value in MANIFESTATION_CATEGORIES


def is_valid_dietary_style(value: str) -> bool:
    return value in DIETARY_STYLES
