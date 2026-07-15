"""Core configuration settings."""
import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_NAME: str = "E-commerce"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ecommerce.db"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "*"

    # Frontend
    FRONTEND_URL: str = "http://localhost:8000"

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Payments
    PAYMENT_PROVIDER: Literal["mock", "enzona"] = "mock"
    PAYMENT_MODE: Literal["sandbox", "live"] = "sandbox"
    PAYMENT_WEBHOOK_SECRET: str = "mock-webhook-secret"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
