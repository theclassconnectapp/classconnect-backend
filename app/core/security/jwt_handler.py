from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config.app_settings import settings


def _make_token(uid: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": uid,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": token_type,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(uid: str) -> str:
    return _make_token(
        uid, "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(uid: str) -> str:
    return _make_token(
        uid, "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Returns uid if valid, None if invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != token_type:
            return None
        uid: Optional[str] = payload.get("sub")
        return uid
    except JWTError:
        return None
