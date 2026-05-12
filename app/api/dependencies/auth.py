"""Reusable authentication dependencies."""

from collections.abc import Callable

from fastapi import Cookie, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.security import decode_token, validate_scopes
from app.db.models import User
from app.db.session import get_session


bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    cookie_token: str | None,
) -> str | None:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return cookie_token


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    session: Session = Depends(get_session),
) -> User:
    """Return authenticated user or raise 401.

    Never returns None.
    """
    token = _extract_token(credentials, cookie_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = session.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return user


def require_scopes(required_scopes: list[str]) -> Callable:
    """Dependency factory validating required scopes by inclusion."""

    def _scope_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not validate_scopes(current_user.scopes, required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope",
            )
        return current_user

    return _scope_dependency
