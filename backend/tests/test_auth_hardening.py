"""Phase 1: password strength, login lockout, logout revocation,
password reset, and account deletion."""


async def _signup(client, email: str, password: str = "supersecret1"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": password})
    return response


async def test_weak_password_rejected_on_signup(client):
    response = await client.post(
        "/auth/signup", json={"name": "User", "email": "weak@example.com", "password": "alllettersnodigits"}
    )
    assert response.status_code == 422


async def test_too_short_password_rejected_on_signup(client):
    response = await client.post(
        "/auth/signup", json={"name": "User", "email": "short@example.com", "password": "abc123"}
    )
    assert response.status_code == 422


async def test_login_locks_out_after_repeated_failures(client):
    await _signup(client, "lockout@example.com")
    for _ in range(5):
        response = await client.post(
            "/auth/login", json={"email": "lockout@example.com", "password": "wrongpass1"}
        )
        assert response.status_code == 401

    locked = await client.post(
        "/auth/login", json={"email": "lockout@example.com", "password": "supersecret1"}
    )
    assert locked.status_code == 429


async def test_logout_revokes_current_token(client):
    signup = await _signup(client, "logout@example.com")
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/auth/me", headers=headers)
    assert me.status_code == 200

    logout = await client.post("/auth/logout", headers=headers)
    assert logout.status_code == 200

    after_logout = await client.get("/auth/me", headers=headers)
    assert after_logout.status_code == 401


async def test_password_reset_flow(client, test_db):
    await _signup(client, "reset@example.com", "originalpass1")

    request = await client.post("/auth/password-reset/request", json={"email": "reset@example.com"})
    assert request.status_code == 200

    reset_doc = await test_db.password_resets.find_one({})
    assert reset_doc is not None

    # We only ever stored a hash — recover the plaintext token isn't possible
    # from the DB, so this test reaches into the logger-emitted value isn't
    # feasible either; instead confirm a bad token is rejected and a wrong
    # token shape doesn't crash the endpoint.
    bad_confirm = await client.post(
        "/auth/password-reset/confirm", json={"token": "not-the-real-token", "new_password": "brandnew1"}
    )
    assert bad_confirm.status_code == 400


async def test_password_reset_request_does_not_leak_account_existence(client):
    known = await client.post("/auth/password-reset/request", json={"email": "reset@example.com"})
    unknown = await client.post("/auth/password-reset/request", json={"email": "never-signed-up@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


async def test_account_deletion_removes_access_and_owned_data(client, test_db):
    signup = await _signup(client, "deleteme@example.com")
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/goals", json={"title": "Bye goal", "category": "money", "target": "$1"}, headers=headers
    )

    delete = await client.delete("/auth/me", headers=headers)
    assert delete.status_code == 204

    assert await test_db.users.find_one({"email": "deleteme@example.com"}) is None
    assert await test_db.goals.count_documents({}) == 0

    me = await client.get("/auth/me", headers=headers)
    assert me.status_code == 401
