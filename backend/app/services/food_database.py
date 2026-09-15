FOODS = [
    {"name": "Grilled chicken breast", "calories": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 4, "emoji": "🍗"},
    {"name": "Avocado toast", "calories": 250, "protein_g": 6, "carbs_g": 28, "fat_g": 14, "emoji": "🥑"},
    {"name": "Greek yogurt", "calories": 130, "protein_g": 18, "carbs_g": 9, "fat_g": 3, "emoji": "🥣"},
    {"name": "Overnight oats", "calories": 300, "protein_g": 10, "carbs_g": 45, "fat_g": 8, "emoji": "🥣"},
    {"name": "Salmon fillet", "calories": 280, "protein_g": 34, "carbs_g": 0, "fat_g": 15, "emoji": "🐟"},
    {"name": "Brown rice (1 cup)", "calories": 215, "protein_g": 5, "carbs_g": 45, "fat_g": 2, "emoji": "🍚"},
    {"name": "Quinoa (1 cup)", "calories": 220, "protein_g": 8, "carbs_g": 39, "fat_g": 4, "emoji": "🌾"},
    {"name": "Mixed berries", "calories": 85, "protein_g": 1, "carbs_g": 21, "fat_g": 0, "emoji": "🍓"},
    {"name": "Almonds (1 oz)", "calories": 165, "protein_g": 6, "carbs_g": 6, "fat_g": 14, "emoji": "🌰"},
    {"name": "Protein shake", "calories": 150, "protein_g": 25, "carbs_g": 8, "fat_g": 2, "emoji": "🥤"},
    {"name": "Caesar salad", "calories": 320, "protein_g": 12, "carbs_g": 14, "fat_g": 24, "emoji": "🥗"},
    {"name": "Turkey wrap", "calories": 380, "protein_g": 28, "carbs_g": 40, "fat_g": 12, "emoji": "🌯"},
    {"name": "Egg (whole)", "calories": 78, "protein_g": 6, "carbs_g": 1, "fat_g": 5, "emoji": "🥚"},
    {"name": "Banana", "calories": 105, "protein_g": 1, "carbs_g": 27, "fat_g": 0, "emoji": "🍌"},
    {"name": "Sweet potato (medium)", "calories": 112, "protein_g": 2, "carbs_g": 26, "fat_g": 0, "emoji": "🍠"},
    {"name": "Dark chocolate square", "calories": 70, "protein_g": 1, "carbs_g": 7, "fat_g": 5, "emoji": "🍫"},
    {"name": "Hummus & veggies", "calories": 180, "protein_g": 6, "carbs_g": 18, "fat_g": 10, "emoji": "🥒"},
    {"name": "Shrimp stir fry", "calories": 310, "protein_g": 28, "carbs_g": 22, "fat_g": 12, "emoji": "🍤"},
    {"name": "Lentil soup", "calories": 230, "protein_g": 14, "carbs_g": 36, "fat_g": 3, "emoji": "🍲"},
    {"name": "Cottage cheese", "calories": 110, "protein_g": 14, "carbs_g": 4, "fat_g": 4, "emoji": "🧀"},
]


def search_foods(query: str) -> list[dict]:
    lowered = query.lower().strip()
    if not lowered:
        return FOODS[:10]
    return [f for f in FOODS if lowered in f["name"].lower()][:15]


def foods_fitting_budget(remaining_calories: float, remaining_protein: float) -> list[dict]:
    candidates = [f for f in FOODS if f["calories"] <= max(remaining_calories, 120)]
    candidates.sort(key=lambda f: (abs(f["calories"] - remaining_calories), -f["protein_g"]))
    return candidates
