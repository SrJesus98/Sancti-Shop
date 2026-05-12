"""Security utilities: JWT, password hashing, scopes."""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


# JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# Scopes
def validate_scopes(user_scopes: list[str], required_scopes: list[str]) -> bool:
    """
    Validate that user has all required scopes.
    Validates by inclusion: required ⊆ user.scopes
    """
    user_scopes_set = set(user_scopes)
    required_scopes_set = set(required_scopes)
    return required_scopes_set.issubset(user_scopes_set)


# Roles
class UserRole:
    """User roles constants."""
    USER = "user"
    ADMIN = "admin"


class OrderStatus:
    """Order status constants."""
    EN_PROCESO = "En proceso"
    PAGADA = "Pagada"
    LISTA = "Lista"
    ENTREGADA = "Entregada"
