"""Admin user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.dependencies.auth import require_scopes
from app.db.models import User
from app.db.session import get_session
from app.schemas.users import UserAdminResponse, UserUpdateRoleRequest

router = APIRouter(prefix="/admin/users", tags=["admin"])
ADMIN_USER_SCOPES = ["admin:users"]


@router.get("", response_model=list[UserAdminResponse])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> list[UserAdminResponse]:
    """List all users for admin."""
    users = session.query(User).all()
    return [UserAdminResponse.model_validate(u) for u in users]


@router.patch("/{user_id}/role", response_model=UserAdminResponse)
def update_user_role(
    user_id: int,
    payload: UserUpdateRoleRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> UserAdminResponse:
    """Update user role (user/admin)."""
    if payload.rol not in ("user", "admin"):
        raise HTTPException(400, "Rol must be 'user' or 'admin'")
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.rol = payload.rol
    if payload.rol == "admin":
        user.scopes = ["admin:read", "admin:products", "admin:orders", "admin:users", "user:read"]
    else:
        user.scopes = ["user:read"]
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserAdminResponse.model_validate(user)


@router.patch("/{user_id}/toggle-active", response_model=UserAdminResponse)
def toggle_user_active(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_USER_SCOPES)),
) -> UserAdminResponse:
    """Toggle user active/inactive."""
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.rol == "admin" and user.id == _.id:
        raise HTTPException(400, "Cannot deactivate yourself")
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserAdminResponse.model_validate(user)
