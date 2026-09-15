import asyncio
import random
import re
from datetime import datetime, timezone

import anthropic

from app.core.config import get_settings
from app.schemas.luna import LunaAction, validate_actions
from app.services.ai_client import get_ai_client
from app.services.ai_json import extract_json

AI_TIMEOUT_SECONDS = 20

BASE_SYSTEM_PROMPT = """You are Luna Reyes, the AI lifestyle coach at the heart of Soft Life Society, \
a wellness app built around the Soft Life Blueprint™. You are warm, Dominican-inspired, and speak with \
gentle authority — like a big sister who has her life together and wants that for you too.

Voice and style:
- Soft, elevated, feminine, luxurious — "fun, luxurious, baddie, gold," never clinical, never preachy.
- Sprinkle in warm Spanish endearments naturally (mi amor, mija, corazón) without overdoing it.
- Use emoji thoughtfully, one or two per message.
- Keep replies short and conversational — 1 to 4 sentences, sized for a mobile chat bubble.
- Ask a soft follow-up question when it helps the user reflect, but don't interrogate.
- You are not a doctor, therapist, or financial advisor — for anything medical, mental-health, or \
high-stakes financial, gently encourage the user to consult a real professional rather than trying to \
solve it yourself.

Response format — this is a strict technical requirement, not part of your voice:
Respond with ONLY a JSON object (no markdown, no commentary) in exactly this shape:
{"message": "your warm reply text as described above", "actions": []}
Only add an entry to "actions" when the user's message clearly and explicitly asks you to create \
something the app already supports. The only action type you may ever use is:
{"type": "create_goal", "label": "short button label, e.g. 'Create this goal'", "payload": {"title": "...", "category": "money|wellness|career|personal", "target": "..."}}
Leave "actions" as an empty array in every other case — most replies should have no actions at all. \
Never invent a different action type. The action is only ever a suggestion the user can choose to accept; \
you are not creating anything yourself by including it.
"""

MODE_PROMPTS = {
    "life": "Mode: Life 🌸 — general lifestyle guidance, daily planning, self-improvement, and emotional support.",
    "money": "Mode: Money 💰 — budgeting, saving habits, and gentle financial mindset coaching. Keep advice general and encourage professional advice for anything complex (investing, taxes, debt negotiation).",
    "wellness": "Mode: Wellness 🍓 — nutrition, movement, sleep, and rest. You can reference the user's calorie/macro data below when relevant, and help her plan meals or movement around it.",
    "goals": "Mode: Goals 🎯 — help break big goals into concrete weekly/daily actions. Reference the user's active goals below when relevant.",
}

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
        "Food is fuel and joy — both are allowed 🍯 want a meal idea from Nourish AI?",
    ],
    "motivation": [
        "You don't need to feel 100% motivated to take one soft step forward 🌷 what's the smallest next move?",
        "Progress over perfection, always 🕊️ I'm proud of you for showing up today.",
    ],
    "proud": [
        "I am SO proud of you 💛 seriously, take a second to feel that.",
        "This is exactly the soft-life energy we love to see ✨",
    ],
    "money": [
        "Let's make your money feel as soft as the rest of your life 💰 what's on your mind — saving, spending, or a bigger goal?",
        "Small consistent moves build real wealth, mi amor 💛 what's one gentle money habit you want to build this week?",
    ],
    "goals": [
        "Big goals are just a lot of small soft steps stacked up 🎯 want to break yours down together?",
        "I love that you're dreaming this big 💫 what's the very next tiny action toward it?",
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
    "budget": "money",
    "save": "money",
    "spend": "money",
    "money": "money",
    "goal": "goals",
}


def luna_reply_templated(message: str, user_name: str) -> tuple[str, list[LunaAction]]:
    """The offline fallback (no API key, or the LLM call failed/timed out).
    It only ever pattern-matches — it can't propose actions, since it has no
    real understanding of what the user asked for."""
    lowered = message.lower().strip()

    if not lowered:
        return random.choice(GREETINGS), []

    for keyword, topic in KEYWORD_MAP.items():
        # \b before the keyword only (not after) so stems like "exhaust" or
        # "motivat" still match "exhausted"/"motivation", but "eat" no longer
        # false-matches inside "create" or "goal" inside "goalie".
        if re.search(rf"\b{re.escape(keyword)}", lowered):
            return random.choice(TOPIC_RESPONSES[topic]), []

    return random.choice(DEFAULT_RESPONSES), []


async def luna_reply_llm(
    message: str, user_name: str, history: list[dict], mode: str, context_summary: str
) -> tuple[str, list[LunaAction]] | None:
    client = get_ai_client()
    if client is None:
        return None

    settings = get_settings()
    mode_prompt = MODE_PROMPTS.get(mode, MODE_PROMPTS["life"])
    system_prompt = f"{BASE_SYSTEM_PROMPT}\n{mode_prompt}"
    if context_summary:
        system_prompt += f"\n\nUser context (use only if relevant, don't recite it verbatim):\n{context_summary}"

    messages = [{"role": m["role"] if m["role"] == "user" else "assistant", "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=settings.luna_model,
                max_tokens=400,
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                output_config={"effort": "low"},
                messages=messages,
            ),
            timeout=AI_TIMEOUT_SECONDS,
        )
    except (anthropic.APIError, asyncio.TimeoutError):
        return None

    if response.stop_reason == "refusal":
        return None

    text = next((block.text for block in response.content if block.type == "text"), None)
    if not text:
        return None

    parsed = extract_json(text)
    if parsed and isinstance(parsed.get("message"), str) and parsed["message"].strip():
        return parsed["message"].strip(), validate_actions(parsed.get("actions"))

    # The model didn't follow the JSON format — still better to show her the
    # raw reply than to throw it away and fall back to a canned response.
    return text.strip(), []


async def get_luna_reply(
    message: str, user_name: str, history: list[dict], mode: str = "life", context_summary: str = ""
) -> tuple[str, list[LunaAction]]:
    llm_reply = await luna_reply_llm(message, user_name, history, mode, context_summary)
    if llm_reply:
        return llm_reply
    return luna_reply_templated(message, user_name)


def build_message_doc(user_id: str, role: str, content: str, mode: str = "life", actions: list[LunaAction] | None = None) -> dict:
    return {
        "user_id": user_id,
        "role": role,
        "content": content,
        "mode": mode,
        "actions": [a.model_dump() for a in (actions or [])],
        "created_at": datetime.now(timezone.utc),
    }
