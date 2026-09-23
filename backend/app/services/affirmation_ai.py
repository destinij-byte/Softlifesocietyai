import asyncio
import random

import anthropic

from app.core.config import get_settings
from app.schemas.personalization import AFFIRMATION_CATEGORIES, COACHING_STYLES
from app.services.ai_client import get_ai_client
from app.services.ai_json import extract_json

AI_TIMEOUT_SECONDS = 15
MAX_AFFIRMATION_LENGTH = 220

AFFIRMATION_PROMPT = """You write short, powerful, first-person affirmations for Soft Life Society, a warm, \
feminine, luxury wellness and life-planning app. The voice is Luna Reyes — soft, elevated, never clinical, \
occasional Spanish endearment, never preachy or generic-inspirational-poster.

Respond with ONLY a JSON object (no markdown, no commentary) in exactly this shape:
{"text": "the affirmation, first person, max 25 words, no surrounding quote marks"}
"""

# Offline fallback when no ANTHROPIC_API_KEY is configured or the call fails —
# a small curated pool per category so even the no-AI path is category-aware,
# not a single global rotation shared by every user regardless of what they
# actually chose.
FALLBACK_AFFIRMATIONS: dict[str, list[str]] = {
    "self_worth": [
        "I am worthy of the life I'm building, exactly as I am today.",
        "My worth was never up for negotiation.",
        "I belong in every room I'm becoming ready for.",
    ],
    "confidence": [
        "I trust myself to handle whatever today brings.",
        "I move through the world like I already know my worth.",
        "My confidence doesn't need anyone else's permission.",
    ],
    "money": [
        "Money flows to me with ease, and I use it with intention.",
        "I am building real, lasting financial peace.",
        "Every soft, consistent choice is growing my abundance.",
    ],
    "career": [
        "My work reflects the caliber of woman I'm becoming.",
        "I am exactly where I need to be to build what's next.",
        "I lead my career with clarity, not urgency.",
    ],
    "business": [
        "What I'm building matters, even on the slow days.",
        "I trust the vision even when the timeline isn't clear yet.",
        "My business grows because I show up as her, consistently.",
    ],
    "discipline": [
        "Discipline is just love I give my future self.",
        "I keep the promises I make to myself.",
        "Small, consistent action is how I become her.",
    ],
    "wellness": [
        "I nourish my body like it's someone I love, because it is.",
        "Rest is productive. My peace is not optional.",
        "I move through today with gentleness, not pressure.",
    ],
    "peace": [
        "I choose peace over pressure today.",
        "I release what I can't control and trust what I can.",
        "My calm is not conditional on everything going right.",
    ],
    "relationships": [
        "I show up in my relationships as the woman I'm becoming.",
        "I am safe to be fully myself with the people who matter.",
        "I give and receive love with an open, soft heart.",
    ],
    "personal_growth": [
        "Every version of me got me here — I'm proud of her.",
        "I am allowed to outgrow what no longer fits.",
        "Growth doesn't have to be loud to be real.",
    ],
    "transformation": [
        "I am becoming her, one soft, intentional day at a time.",
        "The woman I'm becoming is already inside me.",
        "This season is quietly rewriting who I am.",
    ],
}

DEFAULT_CATEGORY = "self_worth"


def _fallback_affirmation(category: str | None) -> str:
    pool = FALLBACK_AFFIRMATIONS.get(category or DEFAULT_CATEGORY, FALLBACK_AFFIRMATIONS[DEFAULT_CATEGORY])
    return random.choice(pool)


async def generate_affirmation(
    *,
    category: str | None,
    coaching_style: str | None,
    era_label: str | None,
    top_pillar_labels: list[str],
    becoming: str,
    alignment_why: str | None,
) -> str:
    """AI-personalized when a key is configured, always falls back to a
    category-aware (not just day-of-year) curated line otherwise — never a
    single global rotation shared by every user regardless of what they
    actually chose."""
    client = get_ai_client()
    if client is None:
        return _fallback_affirmation(category)

    category_label = AFFIRMATION_CATEGORIES.get(category or "", {}).get("label", "self-worth")
    style_label = COACHING_STYLES.get(coaching_style or "", {}).get("label")

    context_lines = [f'Category: "{category_label}".']
    if becoming:
        context_lines.append(f'She is becoming: "{becoming}".')
    if era_label:
        context_lines.append(f"She's in her {era_label}.")
    if top_pillar_labels:
        context_lines.append(f"Her current priorities: {', '.join(top_pillar_labels)}.")
    if alignment_why:
        context_lines.append(f"Recent context: {alignment_why}")
    if style_label:
        context_lines.append(f"Match this coaching tone: {style_label}.")

    settings = get_settings()
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=settings.luna_model,
                max_tokens=100,
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": f"{AFFIRMATION_PROMPT}\n\n{' '.join(context_lines)}"}],
            ),
            timeout=AI_TIMEOUT_SECONDS,
        )
    except (anthropic.APIError, asyncio.TimeoutError):
        return _fallback_affirmation(category)

    if response.stop_reason == "refusal":
        return _fallback_affirmation(category)

    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        return _fallback_affirmation(category)

    parsed = extract_json(text)
    candidate = parsed.get("text") if isinstance(parsed, dict) else None
    if not isinstance(candidate, str) or not candidate.strip() or len(candidate) > MAX_AFFIRMATION_LENGTH:
        return _fallback_affirmation(category)

    return candidate.strip().strip('"')
