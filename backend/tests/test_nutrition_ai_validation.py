"""Phase 2: AI-generated meal suggestions must be validated (bounded,
non-negative fields) before they can ever reach a client."""
from app.schemas.nutrition import validate_meal_suggestion


def test_valid_meal_suggestion_passes():
    result = validate_meal_suggestion(
        {"name": "Grilled chicken bowl", "calories": 450, "protein_g": 35, "carbs_g": 40, "fat_g": 12, "emoji": "🍗"}
    )
    assert result is not None
    assert result.calories == 450


def test_negative_calories_are_rejected():
    result = validate_meal_suggestion({"name": "Suspicious", "calories": -100, "protein_g": 10, "carbs_g": 10, "fat_g": 10})
    assert result is None


def test_absurd_calorie_count_is_rejected():
    result = validate_meal_suggestion({"name": "Way too much", "calories": 999999, "protein_g": 10, "carbs_g": 10, "fat_g": 10})
    assert result is None


def test_missing_required_field_is_rejected():
    result = validate_meal_suggestion({"calories": 400, "protein_g": 10, "carbs_g": 10, "fat_g": 10})
    assert result is None


def test_malformed_input_does_not_crash():
    assert validate_meal_suggestion({"name": "x", "calories": "not-a-number", "protein_g": 1, "carbs_g": 1, "fat_g": 1}) is None
    assert validate_meal_suggestion(None) is None
