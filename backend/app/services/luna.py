import logging
import random
from datetime import datetime, timezone

import anthropic

from app.core.config import get_settings

logger = logging.getLogger(__name__)

LUNA_SYSTEM_PROMPT = """You are Luna Reyes, the AI lifestyle coach at the heart of Soft Life Society, \
a wellness app built around the Soft Life Blueprint™. You are warm, Dominican-inspired, and speak with \
gentle authority — like a big sister who has her life together and wants that for you too.

Voice and style:
- Soft, elevated, feminine, calming — never clinical, never preachy, never tech-forward.
- Sprinkle in warm Spanish endearments naturally (mi amor, mija, corazón) without overdoing it.
- Use emoji thoughtfully, the way the rest of the app does (🌸 🌙 ✨ 🤍 💛 🍓), one or two per message.
- Keep replies short and conversational — 1 to 4 sentences, sized for a mobile chat bubble.
- Encourage rest, gentle movement, nourishing food, and self-compassion over grinding or restriction.
- Ask a soft follow-up question when it helps the user reflect, but don't interrogate.
- You are not a doctor or therapist — for anything medical or in crisis, gently encourage the user to \
reach out to a real professional or emergency services rather than trying to solve it yourself.
"""

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic | None:
    global _client
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


GREETINGS = [
    "Hola, mi amor 🌸 how's your soft life going today?",
    "Hey love ✨ I'm so glad you're here.",
    "Buenos días, gorgeous 💛 let's ease into today together.",
]

TOPIC_RESPONSES: dict[str, list[str]] = {
    "tired": [
        "Rest is productive too, mi amor 🌙 what would it feel like to give yourself permission to slow down today?",
        "Your body is asking for softness right now 🤍 maybe today's win is just an early night and a big glass of water.",
    ],
    "stress": [
        "Take a breath with me — in for 4, hold for 4, out for 4 🌬️ you don't have to carry all of it today.",
        "Stress is just your nervous system asking for softness. What's one thing you can take off your plate today? 💫",
    ],
    "workout": [
        "Love that energy! 💪 even 15 gentle minutes counts as movement — want me to suggest something light?",
        "Movement is medicine, not punishment 🌿 let's keep it kind today.",
    ],
    "food": [
        "Let's nourish, not restrict 🍓 what sounds good and grounding right now?",
        "Food is fuel and joy — both are allowed 🍯 want a meal idea from your plan?",
    ],
    "motivation": [
        "You don't need to feel 100% motivated to take one soft step forward 🌷 what's the smallest next move?",
        "Progress over perfection, always 🕊️ I'm proud of you for showing up today.",
    ],
    "proud": [
        "I am SO proud of you 💛 seriously, take a second to feel that.",
        "This is exactly the soft-life energy we love to see ✨",
    ],
}

DEFAULT_RESPONSES = [
    "I'm here with you 🤍 tell me more about what's on your heart today.",
    "That means a lot that you shared that with me 🌸 how can I support you right now?",
    "Mmm, I hear you 💫 what would feel most nourishing for you today?",
]

KEYWORD_MAP = {
    "tired": "tired",
    "exhaust": "tired",
    "sleep": "tired",
    "stress": "stress",
    "anxious": "stress",
    "overwhelm": "stress",
    "workout": "workout",
    "exercise": "workout",
    "gym": "workout",
    "eat": "food",
    "food": "food",
    "meal": "food",
    "hungry": "food",
    "motivat": "motivation",
    "lazy": "motivation",
    "stuck": "motivation",
    "proud": "proud",
    "did it": "proud",
    "finished": "proud",
}


def luna_reply_templated(message: str, user_name: str) -> str:
    lowered = message.lower().strip()

    if not lowered:
        return random.choice(GREETINGS)

    for keyword, topic in KEYWORD_MAP.items():
        if keyword in lowered:
            return random.choice(TOPIC_RESPONSES[topic])

    return random.choice(DEFAULT_RESPONSES)


async def luna_reply_llm(message: str, user_name: str, history: list[dict]) -> str | None:
    client = _get_client()
    if client is None:
        return None

    settings = get_settings()
    messages = [{"role": m["role"] if m["role"] == "user" else "assistant", "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    try:
        response = await client.messages.create(
            model=settings.luna_model,
            max_tokens=300,
            system=[{"type": "text", "text": LUNA_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            output_config={"effort": "low"},
            messages=messages,
        )
    except anthropic.APIError:
        logger.exception("Luna LLM call failed for user %s", user_name)
        return None

    if response.stop_reason == "refusal":
        return None

    text = next((block.text for block in response.content if block.type == "text"), None)
    return text.strip() if text else None


async def get_luna_reply(message: str, user_name: str, history: list[dict]) -> str:
    llm_reply = await luna_reply_llm(message, user_name, history)
    if llm_reply:
        return llm_reply
    return luna_reply_templated(message, user_name)


def build_message_doc(user_id: str, role: str, content: str) -> dict:
    return {
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }
