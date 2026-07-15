"""Tests for the SecurityHeadersMiddleware CSP updates (Google Fonts + connect-src)."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.core.limiter import reset_rate_limiter
from app.db.session import sync_engine as engine
from app.main import app


def reset_db() -> None:
    """Reset database tables and rate limiter for test isolation."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    reset_rate_limiter()


def test_csp_style_src_incluye_google_fonts() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/health")

    csp = response.headers["content-security-policy"]
    assert "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com;" in csp


def test_csp_font_src_incluye_google_fonts_static() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/health")

    csp = response.headers["content-security-policy"]
    assert "font-src 'self' https://fonts.gstatic.com;" in csp


def test_csp_connect_src_incluye_localhost() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/health")

    csp = response.headers["content-security-policy"]
    assert "connect-src 'self' http://localhost:8000 https://localhost:8000;" in csp


def test_csp_conserva_directivas_existentes() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/health")

    csp = response.headers["content-security-policy"]
    assert "default-src 'self';" in csp
    assert "script-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net 'unsafe-inline';" in csp
    assert "img-src 'self' data: https://fastapi.tiangolo.com;" in csp
    assert "frame-ancestors 'none'" in csp


def test_otros_headers_de_seguridad_se_mantienen() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-xss-protection"] == "1; mode=block"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"