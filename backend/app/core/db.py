from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    return get_client()[settings.mongodb_db_name]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ensure_indexes(db: AsyncIOMotorDatabase | None = None) -> None:
    """Create the indexes every query in this app relies on. Safe to call repeatedly
    (create_index is idempotent for an identical spec) — called once at startup."""
    db = db if db is not None else get_db()

    await db.users.create_index("email", unique=True)
    await db.users.create_index("invite_code", unique=True, sparse=True)

    await db.food_logs.create_index([("user_id", 1), ("log_date", 1)])
    await db.water_logs.create_index([("user_id", 1), ("log_date", 1)], unique=True)

    await db.luna_messages.create_index([("user_id", 1), ("mode", 1), ("created_at", 1)])

    await db.goals.create_index([("user_id", 1), ("created_at", -1)])

    await db.routines.create_index([("user_id", 1), ("type", 1)], unique=True)
    await db.affirmations.create_index([("user_id", 1), ("type", 1)], unique=True)

    await db.challenge_participants.create_index([("user_id", 1), ("slug", 1)])
    await db.challenge_participants.create_index([("user_id", 1), ("active", 1)])

    await db.blueprints.create_index("user_id", unique=True)

    await db.luna_memories.create_index([("user_id", 1), ("created_at", -1)])
    await db.luna_rate_limits.create_index("user_id", unique=True)

    await db.login_attempts.create_index("email", unique=True)
    await db.password_resets.create_index("token_hash", unique=True)
    try:
        # TTL indexes aren't meaningfully enforced by mongomock in tests, but are
        # real cleanup against a real MongoDB — best-effort so a test backend
        # that rejects the option doesn't block startup.
        await db.password_resets.create_index("expires_at", expireAfterSeconds=0)
        await db.token_denylist.create_index("expires_at", expireAfterSeconds=0)
    except Exception:
        pass
