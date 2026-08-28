MEAL_PLANS = [
    {
        "id": "soft-reset",
        "title": "Soft Reset",
        "emoji": "🌸",
        "description": "A gentle 3-day reset focused on whole foods, hydration, and ease.",
        "days": 3,
        "meals": {
            "breakfast": "Greek yogurt, berries & honey 🍓",
            "lunch": "Grilled chicken salad with avocado 🥑",
            "dinner": "Baked salmon, quinoa & roasted veggies 🐟",
            "snack": "Almonds & dark chocolate square 🍫",
        },
    },
    {
        "id": "glow-up",
        "title": "Glow Up Week",
        "emoji": "✨",
        "description": "A 7-day plan balancing protein, color, and glow-supporting foods.",
        "days": 7,
        "meals": {
            "breakfast": "Overnight oats with chia & mango 🥭",
            "lunch": "Turkey & hummus wrap with greens 🌯",
            "dinner": "Shrimp stir fry with brown rice 🍤",
            "snack": "Sliced cucumber & tzatziki 🥒",
        },
    },
    {
        "id": "cozy-comfort",
        "title": "Cozy Comfort",
        "emoji": "🍯",
        "description": "Warm, nourishing meals for slower, softer weeks.",
        "days": 5,
        "meals": {
            "breakfast": "Golden milk oatmeal 🥣",
            "lunch": "Lentil soup with crusty bread 🍞",
            "dinner": "Roast chicken, sweet potato & greens 🍗",
            "snack": "Herbal tea & honey toast 🍵",
        },
    },
]


def get_meal_plans() -> list[dict]:
    return MEAL_PLANS


def get_meal_plan(plan_id: str) -> dict | None:
    return next((p for p in MEAL_PLANS if p["id"] == plan_id), None)
