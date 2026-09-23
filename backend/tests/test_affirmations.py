"""2.0 Phase D: personalized affirmations — no ANTHROPIC_API_KEY in tests
(conftest.py sets it empty), so these exercise the offline, category-aware
fallback path rather than the AI path, same as Luna and Nourish AI tests."""


async def _signup(client, email: str = "affirm@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_get_affirmations_generates_and_caches_todays_daily_pick(client):
    headers = await _signup(client)
    first = await client.get("/affirmations/morning", headers=headers)
    assert first.status_code == 200
    body = first.json()
    assert body["daily_affirmation"]
    assert body["daily_affirmation_id"]
    assert body["daily_affirmation_favorited"] is False

    second = await client.get("/affirmations/morning", headers=headers)
    assert second.json()["daily_affirmation_id"] == body["daily_affirmation_id"]  # cached for today, not regenerated


async def test_morning_and_night_get_independent_daily_picks(client):
    headers = await _signup(client, "affirm-independent@example.com")
    morning = await client.get("/affirmations/morning", headers=headers)
    night = await client.get("/affirmations/night", headers=headers)
    assert morning.json()["daily_affirmation_id"] != night.json()["daily_affirmation_id"]


async def test_regenerate_creates_a_new_daily_pick_with_requested_category(client):
    headers = await _signup(client, "affirm-regen@example.com")
    original = await client.get("/affirmations/morning", headers=headers)

    regenerated = await client.post("/affirmations/morning/regenerate", json={"category": "money"}, headers=headers)
    assert regenerated.status_code == 200
    body = regenerated.json()
    assert body["daily_affirmation_id"] != original.json()["daily_affirmation_id"]
    assert body["daily_affirmation_category"] == "money"

    # The regenerated one is now "today's" — GET reflects it.
    fetched = await client.get("/affirmations/morning", headers=headers)
    assert fetched.json()["daily_affirmation_id"] == body["daily_affirmation_id"]


async def test_regenerate_rejects_unknown_category(client):
    headers = await _signup(client, "affirm-badcategory@example.com")
    response = await client.post("/affirmations/morning/regenerate", json={"category": "not-a-real-category"}, headers=headers)
    assert response.status_code == 422


async def test_affirmation_uses_blueprint_default_category_when_none_requested(client):
    headers = await _signup(client, "affirm-default-category@example.com")
    await client.put("/blueprint", json={"affirmation_categories": ["confidence"]}, headers=headers)

    response = await client.get("/affirmations/morning", headers=headers)
    assert response.json()["daily_affirmation_category"] == "confidence"


async def test_history_lists_generated_affirmations_newest_first(client):
    headers = await _signup(client, "affirm-history@example.com")
    await client.get("/affirmations/morning", headers=headers)
    await client.post("/affirmations/morning/regenerate", json={}, headers=headers)

    history = await client.get("/affirmations/morning/history", headers=headers)
    assert history.status_code == 200
    entries = history.json()
    assert len(entries) == 2
    assert entries[0]["created_at"] >= entries[1]["created_at"]


async def test_favorite_toggle_flips_state_and_is_ownership_scoped(client):
    headers_a = await _signup(client, "affirm-fav-a@example.com")
    headers_b = await _signup(client, "affirm-fav-b@example.com")

    daily = await client.get("/affirmations/morning", headers=headers_a)
    history_id = daily.json()["daily_affirmation_id"]

    denied = await client.put(f"/affirmations/morning/history/{history_id}/favorite", headers=headers_b)
    assert denied.status_code == 404

    favorited = await client.put(f"/affirmations/morning/history/{history_id}/favorite", headers=headers_a)
    assert favorited.status_code == 200
    assert favorited.json()["favorited"] is True

    unfavorited = await client.put(f"/affirmations/morning/history/{history_id}/favorite", headers=headers_a)
    assert unfavorited.json()["favorited"] is False


async def test_custom_affirmations_and_journal_still_work(client):
    """Regression check: the pre-existing custom-affirmation and journal
    endpoints must keep working unchanged after the daily-pick rework."""
    headers = await _signup(client, "affirm-regression@example.com")

    created = await client.post("/affirmations/morning/custom", json={"text": "I am the moment."}, headers=headers)
    assert created.status_code == 200
    assert len(created.json()["custom"]) == 1
    custom_id = created.json()["custom"][0]["id"]

    deleted = await client.delete(f"/affirmations/morning/custom/{custom_id}", headers=headers)
    assert deleted.json()["custom"] == []

    journaled = await client.put("/affirmations/morning/journal", json={"text": "Feeling good today."}, headers=headers)
    assert journaled.json()["journal_entry"] == "Feeling good today."


async def test_affirmation_history_is_cross_user_scoped(client):
    headers_a = await _signup(client, "affirm-scope-a@example.com")
    headers_b = await _signup(client, "affirm-scope-b@example.com")

    await client.get("/affirmations/morning", headers=headers_a)
    history_b = await client.get("/affirmations/morning/history", headers=headers_b)
    assert history_b.json() == []
