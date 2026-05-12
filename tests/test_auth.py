"""Auth core tests for phase 1."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.db.session import engine
from app.main import app


def reset_db() -> None:
    """Reset database tables for test isolation."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_registro_exitoso() -> None:
    reset_db()
    client = TestClient(app)

    response = client.post(
        "/api/auth/register",
        json={"email": "user@test.com", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@test.com"
    assert "user:read" in body["scopes"]


def test_login_exitoso() -> None:
    reset_db()
    client = TestClient(app)
    client.post(
        "/api/auth/register",
        json={"email": "login@test.com", "password": "password123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "login@test.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert response.cookies.get("access_token")


def test_token_invalido_retorna_401() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_ruta_protegida_sin_token_retorna_401() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_scope_faltante_retorna_403() -> None:
    reset_db()
    client = TestClient(app)
    client.post(
        "/api/auth/register",
        json={"email": "scope@test.com", "password": "password123"},
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "scope@test.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
