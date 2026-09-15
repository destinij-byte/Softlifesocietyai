"""Phase 7c: Progress/Alignment — a computed score, always paired with a
'why', built from collections that already exist rather than a new store."""


async def _signup(client, email: str = "alignment@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_alignment_for_brand_new_user_is_well_formed(client):
    headers = await _signup(client)
    response = await client.get("/progress/alignment", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["score"] <= 1.0
    assert body["why"]
    assert isinstance(body["pillar_scores"], list)


async def test_alignment_score_rises_with_logged_activity(client):
    headers = await _signup(client, "active@example.com")
    baseline = await client.get("/progress/alignment", headers=headers)

    for _ in range(8):
        await client.post("/nourish/water/add", headers=headers)
    await client.post(
        "/nourish/entries",
        json={"name": "Salad", "calories": 400, "protein_g": 20, "carbs_g": 30, "fat_g": 10, "meal_type": "lunch"},
        headers=headers,
    )
    await client.post("/home/mood", json={"mood": "radiant"}, headers=headers)
    await client.post("/night-reset/today", json={"win": "showed up", "gratitude": "", "tomorrow_focus": ""}, headers=headers)

    active = await client.get("/progress/alignment", headers=headers)
    assert active.json()["score"] >= baseline.json()["score"]


async def test_alignment_is_cross_user_scoped(client):
    headers_a = await _signup(client, "align-a@example.com")
    headers_b = await _signup(client, "align-b@example.com")

    for _ in range(8):
        await client.post("/nourish/water/add", headers=headers_a)

    result_a = await client.get("/progress/alignment", headers=headers_a)
    result_b = await client.get("/progress/alignment", headers=headers_b)
    assert result_a.json()["score"] >= result_b.json()["score"]


async def test_alignment_why_mentions_a_pillar_label(client):
    headers = await _signup(client, "why-check@example.com")
    await client.put(
        "/blueprint",
        json={"era": "money", "becoming": "", "pillars": [{"pillar": "money", "priority": 5}]},
        headers=headers,
    )
    await client.post(
        "/goals",
        json={"title": "Save $1000", "category": "money", "target": "$1000", "pillar": "money"},
        headers=headers,
    )
    response = await client.get("/progress/alignment", headers=headers)
    assert response.status_code == 200
    assert "Money" in response.json()["why"] or "carrying" in response.json()["why"]
