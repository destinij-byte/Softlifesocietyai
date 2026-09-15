"""Phase 3: the Personal Life Blueprint — era + pillar priorities."""


async def _signup(client, email: str = "blueprint@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_pillars_and_eras_catalogs_are_public(client):
    pillars = await client.get("/blueprint/pillars")
    eras = await client.get("/blueprint/eras")
    assert pillars.status_code == 200
    assert eras.status_code == 200
    assert "money" in pillars.json()
    assert "soft_life" in eras.json()


async def test_new_user_gets_an_empty_editable_blueprint(client):
    headers = await _signup(client)
    response = await client.get("/blueprint", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["era"] is None
    assert body["pillars"] == []


async def test_put_blueprint_saves_era_and_pillar_priorities(client):
    headers = await _signup(client)
    payload = {
        "era": "glow_up",
        "current_state": "Overwhelmed but ready",
        "becoming": "Disciplined, confident, financially secure",
        "pillars": [{"pillar": "money", "priority": 5}, {"pillar": "body", "priority": 3}],
    }
    saved = await client.put("/blueprint", json=payload, headers=headers)
    assert saved.status_code == 200
    assert saved.json()["era"] == "glow_up"

    fetched = await client.get("/blueprint", headers=headers)
    assert fetched.json()["pillars"] == payload["pillars"]


async def test_invalid_era_and_pillar_are_rejected(client):
    headers = await _signup(client)
    bad_era = await client.put("/blueprint", json={"era": "not-a-real-era"}, headers=headers)
    assert bad_era.status_code == 422

    bad_pillar = await client.put(
        "/blueprint", json={"pillars": [{"pillar": "vibes", "priority": 3}]}, headers=headers
    )
    assert bad_pillar.status_code == 422


async def test_duplicate_pillar_entries_are_rejected(client):
    headers = await _signup(client)
    response = await client.put(
        "/blueprint",
        json={"pillars": [{"pillar": "money", "priority": 3}, {"pillar": "money", "priority": 5}]},
        headers=headers,
    )
    assert response.status_code == 422


async def test_blueprint_is_cross_user_scoped(client):
    headers_a = await _signup(client, "bp-owner@example.com")
    headers_b = await _signup(client, "bp-other@example.com")

    await client.put("/blueprint", json={"era": "ceo"}, headers=headers_a)

    fetched_b = await client.get("/blueprint", headers=headers_b)
    assert fetched_b.json()["era"] is None
