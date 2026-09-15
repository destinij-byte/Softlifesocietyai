"""Phase 3: goals gain a pillar, a "why", and a Smart Goal breakdown
(target -> monthly -> weekly -> today)."""


async def _signup(client, email: str = "goalpillar@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _create_goal(client, headers, **overrides):
    payload = {"title": "Save $50,000", "category": "money", "target": "$50,000"}
    payload.update(overrides)
    response = await client.post("/goals", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_goal_accepts_pillar_why_and_target_value(client):
    headers = await _signup(client)
    goal = await _create_goal(
        client, headers, pillar="money", why="Financial security means I stop waiting on someone else.", target_value=50000
    )
    assert goal["pillar"] == "money"
    assert goal["target_value"] == 50000
    assert goal["breakdown"] == []


async def test_invalid_pillar_is_rejected(client):
    headers = await _signup(client)
    response = await client.post(
        "/goals", json={"title": "x", "category": "money", "target": "y", "pillar": "not-a-pillar"}, headers=headers
    )
    assert response.status_code == 400


async def test_breakdown_add_toggle_delete(client):
    headers = await _signup(client)
    goal = await _create_goal(client, headers)
    goal_id = goal["id"]

    added = await client.post(
        f"/goals/{goal_id}/breakdown",
        json={"period": "monthly", "label": "Save $4,167 this month", "target": 4167},
        headers=headers,
    )
    assert added.status_code == 200
    item = added.json()["breakdown"][0]
    assert item["period"] == "monthly"
    assert item["done"] is False

    toggled = await client.put(f"/goals/{goal_id}/breakdown/{item['id']}/toggle", headers=headers)
    assert toggled.json()["breakdown"][0]["done"] is True

    deleted = await client.delete(f"/goals/{goal_id}/breakdown/{item['id']}", headers=headers)
    assert deleted.json()["breakdown"] == []


async def test_invalid_breakdown_period_is_rejected(client):
    headers = await _signup(client)
    goal = await _create_goal(client, headers)
    response = await client.post(
        f"/goals/{goal['id']}/breakdown", json={"period": "yearly", "label": "x"}, headers=headers
    )
    assert response.status_code == 400


async def test_breakdown_is_cross_user_scoped(client):
    headers_a = await _signup(client, "bd-owner@example.com")
    headers_b = await _signup(client, "bd-other@example.com")
    goal = await _create_goal(client, headers_a)

    blocked = await client.post(
        f"/goals/{goal['id']}/breakdown", json={"period": "today", "label": "sneaky"}, headers=headers_b
    )
    assert blocked.status_code == 404
