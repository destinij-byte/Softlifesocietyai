"""Phase 7a: Night Reset — the end-of-day check-in that closes the
Action -> Check-in step of the core loop, and feeds tomorrow's Home."""


async def _signup(client, email: str = "nightreset@example.com"):
    response = await client.post("/auth/signup", json={"name": "User", "email": email, "password": "supersecret1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_no_checkin_yet_returns_empty_but_includes_day_summary(client):
    headers = await _signup(client)
    response = await client.get("/night-reset/today", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["completed"] is False
    assert body["win"] == ""
    assert body["day_summary"]["log_date"] == body["log_date"]
    assert body["day_summary"]["calories_goal"] > 0


async def test_submitting_a_checkin_is_reflected_on_refetch(client):
    headers = await _signup(client)
    submitted = await client.post(
        "/night-reset/today",
        json={"win": "Finished the report", "gratitude": "Good coffee", "tomorrow_focus": "Rest"},
        headers=headers,
    )
    assert submitted.status_code == 200
    assert submitted.json()["completed"] is True

    fetched = await client.get("/night-reset/today", headers=headers)
    body = fetched.json()
    assert body["completed"] is True
    assert body["win"] == "Finished the report"
    assert body["tomorrow_focus"] == "Rest"


async def test_resubmitting_same_day_overwrites_not_duplicates(client):
    headers = await _signup(client)
    await client.post("/night-reset/today", json={"win": "First", "gratitude": "", "tomorrow_focus": ""}, headers=headers)
    await client.post("/night-reset/today", json={"win": "Second", "gratitude": "", "tomorrow_focus": ""}, headers=headers)

    fetched = await client.get("/night-reset/today", headers=headers)
    assert fetched.json()["win"] == "Second"


async def test_day_summary_reflects_logged_water_and_ritual(client):
    headers = await _signup(client)
    await client.post("/nourish/water/add", headers=headers)
    await client.post("/nourish/water/add", headers=headers)
    await client.get("/routines/morning", headers=headers)  # creates today's routine

    checkin = await client.get("/night-reset/today", headers=headers)
    summary = checkin.json()["day_summary"]
    assert summary["water_count"] == 2
    assert summary["ritual_total"] > 0
    assert summary["ritual_done"] == 0


async def test_checkin_is_cross_user_scoped(client):
    headers_a = await _signup(client, "night-owner@example.com")
    headers_b = await _signup(client, "night-other@example.com")

    await client.post("/night-reset/today", json={"win": "secret win", "gratitude": "", "tomorrow_focus": ""}, headers=headers_a)

    fetched_b = await client.get("/night-reset/today", headers=headers_b)
    assert fetched_b.json()["completed"] is False


async def test_home_context_surfaces_yesterdays_tomorrow_focus(client, test_db):
    from datetime import date, timedelta

    headers = await _signup(client, "yesterday-focus@example.com")

    # Simulate yesterday's checkin directly (submitting "today" always writes
    # today's date, so this backfills the prior day the same way a real
    # check-in from last night would have landed).
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    from app.core.security import decode_access_token

    token = headers["Authorization"].split(" ")[1]
    user_id = decode_access_token(token)["sub"]

    await test_db.daily_checkins.insert_one(
        {"user_id": user_id, "log_date": yesterday, "win": "", "gratitude": "", "tomorrow_focus": "Deep work on the launch"}
    )

    context = await client.get("/home/context", headers=headers)
    assert context.json()["yesterday_focus"] == "Deep work on the launch"
