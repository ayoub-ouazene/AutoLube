from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token


# auto_error=False so we can raise our own 401 with a consistent message
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    autolube_admin_token: str | None = Cookie(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that verifies the JWT in the Authorization header.
    Returns the decoded token payload on success; raises 401 otherwise.
    """
    # Prefer cookie (frontend path), fall back to Bearer (curl/Swagger).
    token = autolube_admin_token or (
        credentials.credentials if credentials else None
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload