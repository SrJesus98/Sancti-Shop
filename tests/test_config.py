"""Tests for app.core.config.Settings CORS_ORIGINS default change."""

from app.core.config import Settings


def test_cors_origins_default_es_wildcard() -> None:
    settings = Settings()

    assert settings.CORS_ORIGINS == "*"


def test_cors_origins_split_produce_una_sola_entrada_wildcard() -> None:
    """main.py builds CORS allow_origins via CORS_ORIGINS.split(','); ensure the
    wildcard default still produces a single-element list rather than being split
    unexpectedly."""
    settings = Settings()

    origins = settings.CORS_ORIGINS.split(",")

    assert origins == ["*"]


def test_cors_origins_puede_sobrescribirse() -> None:
    settings = Settings(CORS_ORIGINS="http://example.com,http://other.com")

    assert settings.CORS_ORIGINS == "http://example.com,http://other.com"
    assert settings.CORS_ORIGINS.split(",") == ["http://example.com", "http://other.com"]