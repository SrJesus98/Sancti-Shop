"""Admin user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_scopes
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.users import UserAdminResponse, UserUpdateRoleRequest

router = APIRouter(prefix="/admin/users", tags=["admin"])
ADMIN_USER_SCOPES = ["admin:users"]


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
    if payload.rol not in ("user", "admin"):
        raise HTTPException(400, "Rol must be 'user' or 'admin'")
    result = await session.execute(select(User).where(User.id == user_id))
    user  = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.rol = payload.rol
    if payload.rol == "admin":
        user.scopes = ["admin:read", "admin:products", "admin:orders", "admin:users", "user:read"]
    else:
        user.scopes = ["user:read"]
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserAdminResponse.model_validate(user)


@router.patch("/{user_id}/toggle-active", response_model=UserAdminResponse)
async def toggle_user_active(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> UserAdminResponse:
    """Toggle user active/inactive."""
    result = await session.execute(select(User).where(User.id == user_id))
    user  = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if user.rol == "admin" and user.id == _.id:
        raise HTTPException(400, "Cannot deactivate yourself")
    user.is_active = not user.is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserAdminResponse.model_validate(user)
