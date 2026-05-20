"""User admin request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    rol: str
    is_active: bool
    scopes: list[str]
    created_at: datetime


class UserUpdateRoleRequest(BaseModel):
    rol: str
