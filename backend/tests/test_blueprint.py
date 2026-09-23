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


async def test_new_catalog_endpoints_are_public(client):
    for path in ("/blueprint/coaching-styles", "/blueprint/motivation-styles", "/blueprint/affirmation-categories", "/blueprint/manifestation-categories", "/blueprint/dietary-styles"):
        response = await client.get(path)
        assert response.status_code == 200
        assert len(response.json()) > 0


async def test_personalization_fields_default_to_empty(client):
    headers = await _signup(client, "personalization-default@example.com")
    response = await client.get("/blueprint", headers=headers)
    body = response.json()
    assert body["preferred_name"] is None
    assert body["coaching_style"] is None
    assert body["motivation_style"] is None
    assert body["affirmation_categories"] == []
    assert body["manifestation_categories"] == []
    assert body["nutrition_preferences"] == {"dietary_style": None, "notes": ""}


async def test_put_blueprint_saves_personalization_fields(client):
    headers = await _signup(client, "personalization-save@example.com")
    payload = {
        "era": "wellness",
        "preferred_name": "Des",
        "coaching_style": "direct",
        "motivation_style": "accountability",
        "affirmation_categories": ["confidence", "money"],
        "manifestation_categories": ["financial_freedom"],
        "nutrition_preferences": {"dietary_style": "vegetarian", "notes": "No mushrooms"},
    }
    saved = await client.put("/blueprint", json=payload, headers=headers)
    assert saved.status_code == 200
    body = saved.json()
    assert body["preferred_name"] == "Des"
    assert body["coaching_style"] == "direct"
    assert body["affirmation_categories"] == ["confidence", "money"]
    assert body["nutrition_preferences"]["dietary_style"] == "vegetarian"

    fetched = await client.get("/blueprint", headers=headers)
    assert fetched.json()["coaching_style"] == "direct"


async def test_invalid_personalization_values_are_rejected(client):
    headers = await _signup(client, "personalization-invalid@example.com")

    bad_coaching = await client.put("/blueprint", json={"coaching_style": "not-a-style"}, headers=headers)
    assert bad_coaching.status_code == 422

    bad_motivation = await client.put("/blueprint", json={"motivation_style": "not-a-style"}, headers=headers)
    assert bad_motivation.status_code == 422

    bad_affirmation_category = await client.put("/blueprint", json={"affirmation_categories": ["not-a-category"]}, headers=headers)
    assert bad_affirmation_category.status_code == 422

    bad_manifestation_category = await client.put("/blueprint", json={"manifestation_categories": ["not-a-category"]}, headers=headers)
    assert bad_manifestation_category.status_code == 422

    bad_dietary_style = await client.put("/blueprint", json={"nutrition_preferences": {"dietary_style": "carnivore-extreme"}}, headers=headers)
    assert bad_dietary_style.status_code == 422
