"""Phase 5: the Home daily-mood check-in."""


async def _signup(client, email: str = "mood@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_mood_options_are_public(client):
    response = await client.get("/home/mood/options")
    assert response.status_code == 200
    assert "radiant" in response.json()


async def test_no_mood_logged_yet_returns_null(client):
    headers = await _signup(client)
    response = await client.get("/home/mood", headers=headers)
    assert response.status_code == 200
    assert response.json()["mood"] is None


async def test_setting_and_updating_mood(client):
    headers = await _signup(client)
    first = await client.post("/home/mood", json={"mood": "tired"}, headers=headers)
    assert first.status_code == 200
    assert first.json()["mood"] == "tired"

    updated = await client.post("/home/mood", json={"mood": "radiant"}, headers=headers)
    assert updated.json()["mood"] == "radiant"

    fetched = await client.get("/home/mood", headers=headers)
    assert fetched.json()["mood"] == "radiant"


async def test_invalid_mood_is_rejected(client):
    headers = await _signup(client)
    response = await client.post("/home/mood", json={"mood": "furious"}, headers=headers)
    assert response.status_code == 400


async def test_mood_is_cross_user_scoped(client):
    headers_a = await _signup(client, "mood-owner@example.com")
    headers_b = await _signup(client, "mood-other@example.com")

    await client.post("/home/mood", json={"mood": "calm"}, headers=headers_a)

    fetched_b = await client.get("/home/mood", headers=headers_b)
    assert fetched_b.json()["mood"] is None


async def test_home_context_is_empty_for_new_user(client):
    headers = await _signup(client, "context-new@example.com")
    response = await client.get("/home/context", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["era"] is None
    assert body["top_pillars"] == []


async def test_home_context_reflects_blueprint(client):
    headers = await _signup(client, "context-set@example.com")
    await client.put(
        "/blueprint",
        json={"era": "money", "becoming": "Financially free", "pillars": [{"pillar": "money", "priority": 5}]},
        headers=headers,
    )
    response = await client.get("/home/context", headers=headers)
    body = response.json()
    assert body["era"] == "money"
    assert body["era_label"] == "Money Era"
    assert body["top_pillars"][0]["pillar"] == "money"
