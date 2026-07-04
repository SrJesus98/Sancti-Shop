"""Authentication endpoints — ASYNC."""

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_scopes
from app.core.limiter import limiter
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.auth import AuthUserResponse, TokenResponse, UserLoginRequest, UserRegisterRequest
from app.services.auth import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: Request,
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_async_session),
) -> AuthUserResponse:
    """Register a user with bcrypt password hashing."""
    user = await register_user(session, payload.email, payload.password)
    return AuthUserResponse(id=user.id, email=user.email, scopes=user.scopes)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: UserLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Authenticate user and issue JWT in body + HttpOnly cookie."""
    token = await login_user(session, payload.email, payload.password)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="strict",
        max_age=60 * 30,
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AuthUserResponse)
async def me(current_user: User = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse(id=current_user.id, email=current_user.email, scopes=current_user.scopes)


@router.get("/admin", response_model=AuthUserResponse)
async def admin_only(
    current_user: User = Depends(require_scopes(["admin:read"])),
) -> AuthUserResponse:
    return AuthUserResponse(id=current_user.id, email=current_user.email, scopes=current_user.scopes)


@router.get("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/views/")
    response.delete_cookie(key="access_token", path="/", secure=False, httponly=True, samesite="strict")
    return response