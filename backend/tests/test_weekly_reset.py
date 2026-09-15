"""Phase 7d: Weekly Reset — a fully computed, read-mostly aggregator over
7 days of existing collections. No new primary data store."""


async def _signup(client, email: str = "weekly@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_weekly_reset_for_new_user_is_well_formed(client):
    headers = await _signup(client)
    response = await client.get("/weekly-reset/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["days"]) == 7
    assert body["week_end"] == body["days"][-1]["log_date"]
    assert body["checkins_completed"] == 0
    assert body["best_day"] is None
    assert "score" in body["alignment"]


async def test_weekly_reset_reflects_logged_activity(client):
    headers = await _signup(client, "weekly-active@example.com")
    for _ in range(4):
        await client.post("/nourish/water/add", headers=headers)
    await client.post("/home/mood", json={"mood": "good"}, headers=headers)
    await client.post("/night-reset/today", json={"win": "x", "gratitude": "", "tomorrow_focus": ""}, headers=headers)
    await client.get("/routines/morning", headers=headers)

    response = await client.get("/weekly-reset/summary", headers=headers)
    body = response.json()
    assert body["mood_days_logged"] == 1
    assert body["checkins_completed"] == 1
    assert body["water_avg_pct"] > 0
    assert body["best_day"] is not None


async def test_weekly_reset_best_day_is_none_when_a_routine_exists_but_untouched(client):
    headers = await _signup(client, "weekly-untouched@example.com")
    await client.get("/routines/morning", headers=headers)  # creates today's routine, 0 steps done

    response = await client.get("/weekly-reset/summary", headers=headers)
    assert response.json()["best_day"] is None


async def test_weekly_reset_includes_challenge_checkins_this_week(client):
    headers = await _signup(client, "weekly-challenge@example.com")
    await client.post("/challenges/water-intake/join", json={}, headers=headers)
    await client.post("/challenges/water-intake/log-today", headers=headers)

    response = await client.get("/weekly-reset/summary", headers=headers)
    challenges = response.json()["challenges"]
    assert len(challenges) == 1
    assert challenges[0]["check_ins_this_week"] == 1


async def test_weekly_reset_includes_goals_overview(client):
    headers = await _signup(client, "weekly-goals@example.com")
    await client.post("/goals", json={"title": "Save $1000", "category": "money", "target": "$1000"}, headers=headers)

    response = await client.get("/weekly-reset/summary", headers=headers)
    goals_overview = response.json()["goals_overview"]
    assert len(goals_overview) == 1
    assert goals_overview[0]["title"] == "Save $1000"


async def test_weekly_reset_is_cross_user_scoped(client):
    headers_a = await _signup(client, "weekly-a@example.com")
    headers_b = await _signup(client, "weekly-b@example.com")

    await client.post("/goals", json={"title": "A's goal", "category": "personal", "target": "x"}, headers=headers_a)

    result_b = await client.get("/weekly-reset/summary", headers=headers_b)
    assert result_b.json()["goals_overview"] == []
