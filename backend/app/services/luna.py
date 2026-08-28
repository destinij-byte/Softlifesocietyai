import random
from datetime import datetime, timezone

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


def luna_reply(message: str, user_name: str) -> str:
    lowered = message.lower().strip()

    if not lowered:
        return random.choice(GREETINGS)

    for keyword, topic in KEYWORD_MAP.items():
        if keyword in lowered:
            return random.choice(TOPIC_RESPONSES[topic])

    return random.choice(DEFAULT_RESPONSES)


def build_message_doc(user_id: str, role: str, content: str) -> dict:
    return {
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }
