from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.db import get_db
from app.core.security import decode_access_token
from app.core.time_utils import ensure_aware

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    jti = payload.get("jti")
    if jti and await db.token_denylist.find_one({"jti": jti}):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended, please log in again")

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_valid_after = user.get("token_valid_after")
    issued_at = payload.get("iat")
    if token_valid_after and issued_at is not None:
        issued_at_dt = datetime.fromtimestamp(issued_at, tz=timezone.utc)
        if issued_at_dt < ensure_aware(token_valid_after):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended, please log in again")

    return user
