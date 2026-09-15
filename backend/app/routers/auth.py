import logging
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import bearer_scheme, get_current_user
from app.core.time_utils import ensure_aware, utcnow
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageOut,
    PasswordResetConfirm,
    PasswordResetRequest,
    SignUpRequest,
    UserOut,
)
from app.services.users import serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("soft_life_society")

LOGIN_ATTEMPT_LIMIT = 5
LOGIN_LOCKOUT_MINUTES = 15
RESET_TOKEN_EXPIRE_MINUTES = 30

# Collections that own per-user data and must be cleared on account deletion.
_USER_OWNED_COLLECTIONS = (
    "goals",
    "routines",
    "affirmations",
    "luna_messages",
    "food_logs",
    "water_logs",
    "challenge_participants",
    "luna_memories",
    "blueprints",
    "moods",
    "daily_checkins",
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def _check_login_lockout(db: AsyncIOMotorDatabase, email: str) -> None:
    record = await db.login_attempts.find_one({"email": email})
    if record and record.get("locked_until") and ensure_aware(record["locked_until"]) > utcnow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in a few minutes.",
        )


async def _register_failed_login(db: AsyncIOMotorDatabase, email: str) -> None:
    record = await db.login_attempts.find_one({"email": email})
    count = (record.get("count", 0) if record else 0) + 1
    update = {"count": count}
    if count >= LOGIN_ATTEMPT_LIMIT:
        update["locked_until"] = utcnow() + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        update["count"] = 0
    await db.login_attempts.update_one({"email": email}, {"$set": update}, upsert=True)


async def _clear_login_attempts(db: AsyncIOMotorDatabase, email: str) -> None:
    await db.login_attempts.delete_one({"email": email})


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignUpRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = _normalize_email(payload.email)
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists")

    settings = get_settings()
    now = utcnow()
    user_doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "avatar_emoji": "🌸",
        "created_at": now,
        "trial_started_at": now,
        "trial_ends_at": now + timedelta(days=settings.trial_length_days),
        "subscription_status": "trialing",
        "subscription_tier": None,
        "friend_ids": [],
        # Floored to whole seconds: JWT `iat` loses sub-second precision on
        # encode, so comparing against a microsecond-precision timestamp set
        # moments earlier in the same request would spuriously reject the
        # token this same signup just issued.
        "token_valid_after": now.replace(microsecond=0),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token(str(result.inserted_id))
    return AuthResponse(access_token=token, user=serialize_user(user_doc))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = _normalize_email(payload.email)
    await _check_login_lockout(db, email)

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        if user:
            await _register_failed_login(db, email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    await _clear_login_attempts(db, email)
    token = create_access_token(str(user["_id"]))
    return AuthResponse(access_token=token, user=serialize_user(user))


@router.post("/logout", response_model=MessageOut)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Revokes only this token (this device/session) — not every session the
    user has open, which is what token_valid_after is for (password reset)."""
    payload = decode_access_token(credentials.credentials) if credentials else None
    if payload and payload.get("jti") and payload.get("exp"):
        await db.token_denylist.insert_one(
            {
                "jti": payload["jti"],
                "user_id": str(current_user["_id"]),
                "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None),
            }
        )
    return MessageOut(message="Logged out.")


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return serialize_user(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    user_id = str(current_user["_id"])
    for collection in _USER_OWNED_COLLECTIONS:
        await db[collection].delete_many({"user_id": user_id})
    await db.users.delete_one({"_id": current_user["_id"]})
    return None


@router.post("/password-reset/request", response_model=MessageOut)
async def request_password_reset(payload: PasswordResetRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Always returns the same message whether or not the email exists, so a
    caller can't use this endpoint to discover registered accounts."""
    email = _normalize_email(payload.email)
    user = await db.users.find_one({"email": email})
    if user:
        token, token_hash = generate_reset_token()
        await db.password_resets.insert_one(
            {
                "user_id": str(user["_id"]),
                "token_hash": token_hash,
                "expires_at": utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
                "used": False,
            }
        )
        # TODO(email): wire a transactional email provider (SendGrid, Postmark,
        # etc.) before this ships to production — for now the reset token only
        # ever reaches the requester via this server log line (dev-mode only).
        logger.info("Password reset requested for %s — token: %s", email, token)

    return MessageOut(message="If that email has an account, we've sent reset instructions.")


@router.post("/password-reset/confirm", response_model=MessageOut)
async def confirm_password_reset(payload: PasswordResetConfirm, db: AsyncIOMotorDatabase = Depends(get_db)):
    token_hash = hash_reset_token(payload.token)
    record = await db.password_resets.find_one({"token_hash": token_hash, "used": False})
    if not record or ensure_aware(record["expires_at"]) < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That reset link is invalid or has expired")

    now = utcnow().replace(microsecond=0)
    await db.users.update_one(
        {"_id": ObjectId(record["user_id"])},
        {"$set": {"password_hash": hash_password(payload.new_password), "token_valid_after": now}},
    )
    await db.password_resets.update_one({"_id": record["_id"]}, {"$set": {"used": True}})
    return MessageOut(message="Your password has been updated. Please log in again.")
