import time
from typing import Any

import bcrypt
import jwt

from app.config import settings


ALGORITHM = "HS256"


# ---------- password verification ----------

def verify_password(plain_password: str) -> bool:
    """Compare a plaintext password against the hash stored in settings."""
    if not plain_password:
        return False
    try:
        stored = settings.admin_password_hash.encode("utf-8")
        provided = plain_password.encode("utf-8")
        return bcrypt.checkpw(provided, stored)
    except (ValueError, TypeError):
        # Malformed hash in .env, or wrong encoding — treat as failure
        return False


def verify_credentials(username: str, password: str) -> bool:
    """Return True only if both username and password match the configured admin."""
    if not username or not password:
        return False
    # Username is a plain comparison (constant-time not needed — it's not secret)
    if username != settings.admin_username:
        return False
    return verify_password(password)


# ---------- JWT ----------

def create_access_token(extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT for the admin. Expires per settings.jwt_expire_minutes."""
    now = int(time.time())
    payload = {
        "sub": settings.admin_username,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Return the JWT payload if valid and not expired, else None."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None