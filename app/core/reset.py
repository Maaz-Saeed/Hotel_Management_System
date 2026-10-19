import hashlib
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


def fingerprint(hashed_password: str) -> str:
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def make_reset_token(kind: str, email: str, hashed_password: str, minutes: int = 30) -> str:
    """kind is 'staff' or 'customer'. The fingerprint changes when the password changes,
    so a reset link works only once."""
    payload = {
        "sub": f"reset:{kind}:{email}",
        "fp": fingerprint(hashed_password),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def read_reset_token(token: str, kind: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    prefix = f"reset:{kind}:"
    sub = payload.get("sub", "")
    if not sub.startswith(prefix) or "fp" not in payload:
        return None
    return sub[len(prefix):], payload["fp"]
