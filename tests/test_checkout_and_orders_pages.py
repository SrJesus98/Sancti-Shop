"""Tests for the checkout.html and orders.html templates pointing to the unified
POST/GET /api/orders endpoint (instead of the old /api/orders/checkout and
/api/orders/ paths)."""

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


def _register_and_login(client: TestClient, email: str) -> None:
    password = "Password123!"
    client.post("/api/auth/register", json={"email": email, "password": password})
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    # The login response sets the "access_token" cookie on the shared TestClient,
    # so subsequent requests through the same client are authenticated for views.


def test_checkout_page_usa_endpoint_unificado_api_orders() -> None:
    reset_db()
    client = TestClient(app)
    _register_and_login(client, "checkout-page@test.com")

    response = client.get("/views/checkout")

    assert response.status_code == 200
    assert "fetch('/api/orders', {" in response.text
    assert "orders/checkout" not in response.text


def test_orders_page_usa_endpoint_unificado_api_orders() -> None:
    reset_db()
    client = TestClient(app)
    _register_and_login(client, "orders-page@test.com")

    response = client.get("/views/orders")

    assert response.status_code == 200
    assert "fetch('/api/orders', {" in response.text
    assert "fetch('/api/orders/', {" not in response.text