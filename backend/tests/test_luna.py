"""Phase 2: Luna chat (templated fallback, since no ANTHROPIC_API_KEY is set
in tests), memory CRUD, and rate limiting."""


async def _signup(client, email: str = "luna@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_greeting_has_a_stable_id_not_an_index(client):
    headers = await _signup(client)
    response = await client.get("/luna/messages?mode=life", headers=headers)
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["id"] == "greeting"


async def test_send_message_returns_templated_reply_with_id_and_actions(client):
    headers = await _signup(client)
    response = await client.post("/luna/messages", json={"message": "I'm so tired today", "mode": "life"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "luna"
    assert body["id"] and body["id"] != "greeting"
    assert body["actions"] == []  # the templated fallback never proposes actions
    assert len(body["content"]) > 0


async def test_message_ids_are_unique_across_a_conversation(client):
    headers = await _signup(client)
    await client.post("/luna/messages", json={"message": "hi", "mode": "life"}, headers=headers)
    await client.post("/luna/messages", json={"message": "hi again", "mode": "life"}, headers=headers)
    history = await client.get("/luna/messages?mode=life", headers=headers)
    ids = [m["id"] for m in history.json()]
    assert len(ids) == len(set(ids))


async def test_memory_crud_is_scoped_and_capped(client, test_db):
    headers = await _signup(client)

    created = await client.post("/luna/memory", json={"text": "Prefers oat milk lattes"}, headers=headers)
    assert created.status_code == 201
    memory_id = created.json()["id"]

    listed = await client.get("/luna/memory", headers=headers)
    assert len(listed.json()) == 1

    deleted = await client.delete(f"/luna/memory/{memory_id}", headers=headers)
    assert deleted.status_code == 204

    listed_after = await client.get("/luna/memory", headers=headers)
    assert listed_after.json() == []


async def test_memory_cap_is_enforced(client):
    headers = await _signup(client, "capped@example.com")
    for i in range(20):
        response = await client.post("/luna/memory", json={"text": f"fact {i}"}, headers=headers)
        assert response.status_code == 201
    over_cap = await client.post("/luna/memory", json={"text": "one too many"}, headers=headers)
    assert over_cap.status_code == 400


async def test_luna_rate_limit_returns_429_once_exceeded(client):
    headers = await _signup(client, "ratelimited@example.com")
    for _ in range(40):
        response = await client.post("/luna/messages", json={"message": "hi", "mode": "life"}, headers=headers)
        assert response.status_code == 200
    limited = await client.post("/luna/messages", json={"message": "one more", "mode": "life"}, headers=headers)
    assert limited.status_code == 429


async def test_memory_is_cross_user_scoped(client):
    headers_a = await _signup(client, "memowner@example.com")
    headers_b = await _signup(client, "memintruder@example.com")

    created = await client.post("/luna/memory", json={"text": "secret preference"}, headers=headers_a)
    memory_id = created.json()["id"]

    listed_b = await client.get("/luna/memory", headers=headers_b)
    assert listed_b.json() == []

    delete_by_b = await client.delete(f"/luna/memory/{memory_id}", headers=headers_b)
    assert delete_by_b.status_code == 204  # no-op delete, not an error — but it must not remove A's memory

    listed_a = await client.get("/luna/memory", headers=headers_a)
    assert len(listed_a.json()) == 1
