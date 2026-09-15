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
