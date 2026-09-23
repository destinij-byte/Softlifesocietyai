"""2.0 Phase A: rate limiting on previously-unprotected endpoints (signup,
password-reset-request, AI-cost nutrition endpoints), all sharing the
generic app/core/rate_limit.py limiter Luna's chat limiter already used."""

import io


async def test_signup_is_rate_limited_by_ip(client):
    for i in range(5):
        response = await client.post(
            "/auth/signup", json={"name": "User", "email": f"rl-signup-{i}@example.com", "password": "supersecret1"}
        )
        assert response.status_code == 201

    over_limit = await client.post(
        "/auth/signup", json={"name": "User", "email": "rl-signup-over@example.com", "password": "supersecret1"}
    )
    assert over_limit.status_code == 429


async def test_password_reset_request_is_rate_limited_by_ip(client):
    for _ in range(5):
        response = await client.post("/auth/password-reset/request", json={"email": "nobody@example.com"})
        assert response.status_code == 200

    over_limit = await client.post("/auth/password-reset/request", json={"email": "nobody@example.com"})
    assert over_limit.status_code == 429


async def test_meal_builder_is_rate_limited_by_user(client):
    signup = await client.post(
        "/auth/signup", json={"name": "User", "email": "rl-mealbuilder@example.com", "password": "supersecret1"}
    )
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}

    for _ in range(30):
        response = await client.post("/nourish/meal-builder?meal_type=dinner", headers=headers)
        assert response.status_code == 200

    over_limit = await client.post("/nourish/meal-builder?meal_type=dinner", headers=headers)
    assert over_limit.status_code == 429


async def test_analyze_meal_is_rate_limited_by_user(client):
    signup = await client.post(
        "/auth/signup", json={"name": "User", "email": "rl-analyzemeal@example.com", "password": "supersecret1"}
    )
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    photo = {"photo": ("meal.jpg", io.BytesIO(b"not a real image but small"), "image/jpeg")}

    for _ in range(20):
        response = await client.post("/nourish/analyze-meal", headers=headers, files=photo)
        # No ANTHROPIC_API_KEY in tests, so this 503s rather than 200 — the
        # point here is only that the rate limiter runs before that, not
        # that the analysis itself succeeds.
        assert response.status_code in (200, 503)

    over_limit = await client.post("/nourish/analyze-meal", headers=headers, files=photo)
    assert over_limit.status_code == 429


async def test_rate_limits_are_scoped_per_user_not_global(client):
    signup_a = await client.post(
        "/auth/signup", json={"name": "User", "email": "rl-scope-a@example.com", "password": "supersecret1"}
    )
    headers_a = {"Authorization": f"Bearer {signup_a.json()['access_token']}"}
    for _ in range(30):
        assert (await client.post("/nourish/meal-builder?meal_type=dinner", headers=headers_a)).status_code == 200
    assert (await client.post("/nourish/meal-builder?meal_type=dinner", headers=headers_a)).status_code == 429

    signup_b = await client.post(
        "/auth/signup", json={"name": "User", "email": "rl-scope-b@example.com", "password": "supersecret1"}
    )
    headers_b = {"Authorization": f"Bearer {signup_b.json()['access_token']}"}
    # User B is unaffected by user A's exhausted limit.
    assert (await client.post("/nourish/meal-builder?meal_type=dinner", headers=headers_b)).status_code == 200
