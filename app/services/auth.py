"""Authentication service helpers."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import User


def register_user(session: Session, email: str, password: str) -> User:
    """Create a new user with bcrypt hashed password."""
    existing_user = session.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        scopes=["user:read"],
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(session: Session, email: str, password: str) -> str:
    """Validate credentials and return JWT token."""
    user = session.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return create_access_token({"sub": user.email, "scopes": user.scopes})
