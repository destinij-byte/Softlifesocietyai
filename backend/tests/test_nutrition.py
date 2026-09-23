from datetime import date, datetime, timedelta, timezone

import pytest


@pytest.mark.asyncio
async def test_today_streak_is_zero_with_no_logs(client, auth_headers):
    headers = await auth_headers()
    response = await client.get("/nourish/today", headers=headers)
    assert response.status_code == 200
    assert response.json()["streak"] == 0


@pytest.mark.asyncio
async def test_streak_counts_today_once_logged(client, auth_headers):
    headers = await auth_headers()
    await client.post(
        "/nourish/entries",
        json={"name": "Oatmeal", "calories": 300, "protein_g": 10, "carbs_g": 40, "fat_g": 5, "meal_type": "breakfast"},
        headers=headers,
    )
    response = await client.get("/nourish/today", headers=headers)
    assert response.json()["streak"] == 1


@pytest.mark.asyncio
async def test_streak_counts_consecutive_prior_days(client, auth_headers, test_db):
    headers = await auth_headers()
    me = await client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    today = date.today()
    for offset in range(1, 4):  # yesterday, 2 and 3 days ago logged; today not yet
        log_date = (today - timedelta(days=offset)).isoformat()
        await test_db.food_logs.insert_one(
            {
                "user_id": user_id,
                "name": "Backfilled meal",
                "calories": 200,
                "protein_g": 5,
                "carbs_g": 20,
                "fat_g": 5,
                "meal_type": "snack",
                "emoji": "🍽️",
                "logged_at": datetime.now(timezone.utc),
                "log_date": log_date,
            }
        )

    response = await client.get("/nourish/today", headers=headers)
    assert response.json()["streak"] == 3


@pytest.mark.asyncio
async def test_streak_breaks_on_a_gap(client, auth_headers, test_db):
    headers = await auth_headers()
    me = await client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    today = date.today()
    # yesterday logged, but 2 days ago is a gap -> streak should be 1 (today unlogged, so counts from yesterday)
    await test_db.food_logs.insert_one(
        {
            "user_id": user_id,
            "name": "Meal",
            "calories": 200,
            "protein_g": 5,
            "carbs_g": 20,
            "fat_g": 5,
            "meal_type": "snack",
            "emoji": "🍽️",
            "logged_at": datetime.now(timezone.utc),
            "log_date": (today - timedelta(days=1)).isoformat(),
        }
    )
    await test_db.food_logs.insert_one(
        {
            "user_id": user_id,
            "name": "Meal",
            "calories": 200,
            "protein_g": 5,
            "carbs_g": 20,
            "fat_g": 5,
            "meal_type": "snack",
            "emoji": "🍽️",
            "logged_at": datetime.now(timezone.utc),
            "log_date": (today - timedelta(days=3)).isoformat(),
        }
    )

    response = await client.get("/nourish/today", headers=headers)
    assert response.json()["streak"] == 1


@pytest.mark.asyncio
async def test_streak_is_cross_user_scoped(client, auth_headers, test_db):
    headers_a = await auth_headers(email="streak-a@example.com")
    headers_b = await auth_headers(email="streak-b@example.com")

    me_b = await client.get("/auth/me", headers=headers_b)
    user_b_id = me_b.json()["id"]

    today = date.today()
    for offset in range(1, 6):
        await test_db.food_logs.insert_one(
            {
                "user_id": user_b_id,
                "name": "Meal",
                "calories": 200,
                "protein_g": 5,
                "carbs_g": 20,
                "fat_g": 5,
                "meal_type": "snack",
                "emoji": "🍽️",
                "logged_at": datetime.now(timezone.utc),
                "log_date": (today - timedelta(days=offset)).isoformat(),
            }
        )

    response_a = await client.get("/nourish/today", headers=headers_a)
    assert response_a.json()["streak"] == 0


@pytest.mark.asyncio
async def test_log_date_query_param_returns_that_days_entries(client, auth_headers, test_db):
    headers = await auth_headers()
    me = await client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    await test_db.food_logs.insert_one(
        {
            "user_id": user_id,
            "name": "Yesterday's lunch",
            "calories": 550,
            "protein_g": 20,
            "carbs_g": 60,
            "fat_g": 15,
            "meal_type": "lunch",
            "emoji": "🥗",
            "logged_at": datetime.now(timezone.utc),
            "log_date": yesterday,
        }
    )

    response = await client.get(f"/nourish/today?log_date={yesterday}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["date"] == yesterday
    assert body["total_calories"] == 550
    assert len(body["entries"]) == 1
    assert body["entries"][0]["name"] == "Yesterday's lunch"

    # Today's own (empty) summary is unaffected.
    today_response = await client.get("/nourish/today", headers=headers)
    assert today_response.json()["total_calories"] == 0


@pytest.mark.asyncio
async def test_log_date_future_date_is_clamped_to_today(client, auth_headers):
    headers = await auth_headers()
    future = (date.today() + timedelta(days=5)).isoformat()
    response = await client.get(f"/nourish/today?log_date={future}", headers=headers)
    assert response.status_code == 200
    assert response.json()["date"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_log_date_malformed_falls_back_to_today(client, auth_headers):
    headers = await auth_headers()
    response = await client.get("/nourish/today?log_date=not-a-date", headers=headers)
    assert response.status_code == 200
    assert response.json()["date"] == date.today().isoformat()
