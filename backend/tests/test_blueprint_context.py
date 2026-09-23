"""blueprint_context is the single source of truth every feature reads
instead of querying the blueprints collection directly."""

from app.services.blueprint_context import get_blueprint_context


async def test_no_blueprint_returns_empty_context(test_db):
    ctx = await get_blueprint_context(test_db, "someone")
    assert ctx.era is None
    assert ctx.top_pillars == []
    assert ctx.summary() == ""
    assert ctx.pillar_rank("money") == 0


async def test_top_pillars_are_ranked_by_priority_desc(test_db):
    await test_db.blueprints.insert_one(
        {
            "user_id": "u1",
            "era": "money",
            "becoming": "Financially free",
            "pillars": [
                {"pillar": "growth", "priority": 2},
                {"pillar": "money", "priority": 5},
                {"pillar": "body", "priority": 4},
                {"pillar": "home", "priority": 1},
            ],
            "current_state": "",
            "created_at": None,
            "updated_at": None,
        }
    )

    ctx = await get_blueprint_context(test_db, "u1")
    assert ctx.era_label == "Money Era"
    assert ctx.top_pillars == ["money", "body", "growth"]  # top 3 only, "home" excluded
    assert ctx.pillar_rank("money") == 0
    assert ctx.pillar_rank("body") == 1
    assert ctx.pillar_rank("home") == 3  # unranked pillar sorts after all top pillars
    assert ctx.pillar_rank(None) == 3
    assert "Money Era" in ctx.summary()
    assert "Financially free" in ctx.summary()


async def test_unknown_era_and_pillar_values_are_ignored_gracefully(test_db):
    await test_db.blueprints.insert_one(
        {
            "user_id": "u2",
            "era": "not-a-real-era",
            "becoming": "",
            "pillars": [{"pillar": "not-a-real-pillar", "priority": 5}],
            "current_state": "",
            "created_at": None,
            "updated_at": None,
        }
    )

    ctx = await get_blueprint_context(test_db, "u2")
    assert ctx.era_label is None
    assert ctx.top_pillars == []


async def test_personalization_fields_flow_into_context_and_summary(test_db):
    await test_db.blueprints.insert_one(
        {
            "user_id": "u3",
            "era": "discipline",
            "becoming": "",
            "pillars": [],
            "current_state": "",
            "preferred_name": "Des",
            "coaching_style": "direct",
            "motivation_style": "accountability",
            "affirmation_categories": ["confidence"],
            "manifestation_categories": [],
            "nutrition_preferences": {"dietary_style": "vegetarian", "notes": ""},
            "created_at": None,
            "updated_at": None,
        }
    )

    ctx = await get_blueprint_context(test_db, "u3")
    assert ctx.preferred_name == "Des"
    assert ctx.coaching_style == "direct"
    assert ctx.motivation_style == "accountability"
    assert ctx.dietary_style == "vegetarian"
    assert ctx.affirmation_categories == ["confidence"]

    summary = ctx.summary()
    assert "Des" in summary
    assert "Direct & no-fluff" in summary
    assert "Accountability & structure" in summary


async def test_unknown_coaching_and_motivation_styles_are_ignored_gracefully(test_db):
    await test_db.blueprints.insert_one(
        {
            "user_id": "u4",
            "era": None,
            "becoming": "",
            "pillars": [],
            "current_state": "",
            "coaching_style": "not-a-real-style",
            "motivation_style": "also-not-real",
            "created_at": None,
            "updated_at": None,
        }
    )

    ctx = await get_blueprint_context(test_db, "u4")
    assert ctx.coaching_style is None
    assert ctx.motivation_style is None
