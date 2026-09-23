"""Confirms protected resources are scoped to the authenticated user — the
core invariant the audit flagged as critical (no cross-user data access)."""


async def _signup(client, email: str):
    response = await client.post(
        "/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"}
    )
    assert response.status_code == 201
    return response.json()["access_token"]


async def test_user_cannot_see_or_modify_another_users_goal(client):
    token_a = await _signup(client, "owner@example.com")
    token_b = await _signup(client, "intruder@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    create = await client.post(
        "/goals",
        json={"title": "Save $10k", "category": "money", "target": "$10,000"},
        headers=headers_a,
    )
    assert create.status_code == 201
    goal_id = create.json()["id"]

    # B's own list must not contain A's goal.
    list_b = await client.get("/goals", headers=headers_b)
    assert all(g["id"] != goal_id for g in list_b.json())

    # B cannot bump A's goal progress.
    bump = await client.put(f"/goals/{goal_id}/progress?progress=0.5", headers=headers_b)
    assert bump.status_code == 404

    # B cannot delete A's goal.
    delete = await client.delete(f"/goals/{goal_id}", headers=headers_b)
    assert delete.status_code == 204  # delete_one on a non-matching filter is a no-op, not an error

    # The goal is still there for A, untouched.
    list_a = await client.get("/goals", headers=headers_a)
    assert any(g["id"] == goal_id and g["progress"] == 0 for g in list_a.json())


async def test_malformed_goal_id_returns_400_not_500(client):
    token = await _signup(client, "malformed@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.put("/goals/not-a-valid-objectid/progress?progress=0.5", headers=headers)
    assert response.status_code == 400
