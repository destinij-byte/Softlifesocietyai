import pytest


@pytest.mark.anyio
async def test_signup_login_me(client):
    signup = await client.post(
        "/auth/signup",
        json={"name": "Destini", "email": "destini@example.com", "password": "supersecret1"},
    )
    assert signup.status_code == 201
    body = signup.json()
    assert body["user"]["email"] == "destini@example.com"
    assert "password_hash" not in body["user"]
    token = body["access_token"]

    login = await client.post(
        "/auth/login", json={"email": "destini@example.com", "password": "supersecret1"}
    )
    assert login.status_code == 200

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["name"] == "Destini"


async def test_duplicate_signup_rejected(client):
    payload = {"name": "Destini", "email": "dupe@example.com", "password": "supersecret1"}
    first = await client.post("/auth/signup", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/signup", json=payload)
    assert second.status_code == 409


async def test_wrong_password_rejected(client):
    await client.post(
        "/auth/signup",
        json={"name": "Destini", "email": "wrong@example.com", "password": "supersecret1"},
    )
    login = await client.post("/auth/login", json={"email": "wrong@example.com", "password": "nope"})
    assert login.status_code == 401


async def test_me_requires_auth(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_malformed_token_rejected(client):
    response = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
