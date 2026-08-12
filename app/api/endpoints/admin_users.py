"""Admin user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_scopes
from app.core.security import UserRole
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.users import UserAdminResponse, UserUpdateRoleRequest

router = APIRouter(prefix="/admin/users", tags=["admin"])
ADMIN_USER_SCOPES = ["admin:users"]

ADMIN_FULL_SCOPES = [
    "admin:read",
    "admin:products",
    "admin:orders",
    "admin:users",
    "user:read",
]
USER_DEFAULT_SCOPES = ["user:read"]


@router.get("", response_model=list[UserAdminResponse])
async def list_users(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> list[UserAdminResponse]:
    """List all users for admin."""
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [UserAdminResponse.model_validate(u) for u in users]


@router.patch("/{user_id}/role", response_model=UserAdminResponse)
async def update_user_role(
    user_id: int,
    payload: UserUpdateRoleRequest,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> UserAdminResponse:
    """Update user role (user/admin)."""
    if payload.rol not in (UserRole.USER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rol must be 'user' or 'admin'",
        )
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.rol = payload.rol
    if payload.rol == UserRole.ADMIN:
        user.scopes = ADMIN_FULL_SCOPES
    else:
        user.scopes = USER_DEFAULT_SCOPES
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserAdminResponse.model_validate(user)


@router.patch("/{user_id}/toggle-active", response_model=UserAdminResponse)
async def toggle_user_active(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> UserAdminResponse:
    """Toggle user active/inactive."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.rol == UserRole.ADMIN and user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )
    user.is_active = not user.is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserAdminResponse.model_validate(user)
