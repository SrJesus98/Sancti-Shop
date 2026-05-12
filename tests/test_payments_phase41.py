"""Phase 4.1 payments adapter tests (TDD)."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.db.models import Order, PaymentWebhookEvent, Product, User
from app.db.session import engine
from app.main import app


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _register_and_login(client: TestClient, email: str, as_admin: bool = False) -> dict[str, str]:
    password = "password123"
    client.post("/api/auth/register", json={"email": email, "password": password})

    if as_admin:
        with Session(engine) as session:
            user = session.query(User).filter(User.email == email).first()
            assert user is not None
            user.rol = "admin"
            user.scopes = ["user:read", "admin:products", "admin:orders"]
            session.add(user)
            session.commit()

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_product() -> Product:
    with Session(engine) as session:
        product = Product(name="Phone", description="Smartphone", price=100.0, stock=5, category="tech")
        session.add(product)
        session.commit()
        session.refresh(product)
        return product


def _create_order(client: TestClient, user_headers: dict[str, str]) -> int:
    p = _seed_product()
    client.post("/api/cart/items", headers=user_headers, json={"product_id": p.id, "quantity": 1})
    checkout = client.post("/api/orders/checkout", headers=user_headers)
    assert checkout.status_code == 201
    return checkout.json()["id"]


def test_create_intent_exitoso() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "payer@test.com")
    order_id = _create_order(client, headers)

    response = client.post(
        "/api/payments/create-intent",
        headers=headers,
        json={"order_id": order_id, "simulate": "approved"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["order_id"] == order_id
    assert body["status"] == "pending"
    assert "redirect_url" in body


def test_create_intent_falla_si_orden_no_pertenece() -> None:
    reset_db()
    client = TestClient(app)
    owner_headers = _register_and_login(client, "owner@test.com")
    attacker_headers = _register_and_login(client, "attacker@test.com")
    order_id = _create_order(client, owner_headers)

    response = client.post("/api/payments/create-intent", headers=attacker_headers, json={"order_id": order_id})
    assert response.status_code == 403


def test_webhook_approved_mueve_orden_a_pagada() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "approved@test.com")
    order_id = _create_order(client, headers)
    intent = client.post("/api/payments/create-intent", headers=headers, json={"order_id": order_id}).json()

    response = client.post(
        "/api/payments/webhook",
        headers={"X-Webhook-Signature": "mock-webhook-secret"},
        json={"payment_id": intent["id"], "order_id": order_id, "status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    with Session(engine) as session:
        order = session.query(Order).filter(Order.id == order_id).first()
        assert order is not None
        assert order.status == "Pagada"


def test_webhook_rejected_no_marca_pagada() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "rejected@test.com")
    order_id = _create_order(client, headers)
    intent = client.post("/api/payments/create-intent", headers=headers, json={"order_id": order_id}).json()

    response = client.post(
        "/api/payments/webhook",
        headers={"X-Webhook-Signature": "mock-webhook-secret"},
        json={"payment_id": intent["id"], "order_id": order_id, "status": "rejected"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

    with Session(engine) as session:
        order = session.query(Order).filter(Order.id == order_id).first()
        assert order is not None
        assert order.status == "En proceso"


def test_webhook_duplicado_no_duplica_transicion() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "dup@test.com")
    order_id = _create_order(client, headers)
    intent = client.post("/api/payments/create-intent", headers=headers, json={"order_id": order_id}).json()
    payload = {"payment_id": intent["id"], "order_id": order_id, "status": "approved"}
    signature = {"X-Webhook-Signature": "mock-webhook-secret"}

    first = client.post("/api/payments/webhook", headers=signature, json=payload)
    second = client.post("/api/payments/webhook", headers=signature, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200

    with Session(engine) as session:
        events = session.query(PaymentWebhookEvent).all()
        assert len(events) == 1


def test_webhook_firma_invalida_retorna_401() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "bad-sign@test.com")
    order_id = _create_order(client, headers)
    intent = client.post("/api/payments/create-intent", headers=headers, json={"order_id": order_id}).json()

    response = client.post(
        "/api/payments/webhook",
        headers={"X-Webhook-Signature": "invalid"},
        json={"payment_id": intent["id"], "order_id": order_id, "status": "approved"},
    )
    assert response.status_code == 401


def test_get_payment_status_funciona() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "status@test.com")
    order_id = _create_order(client, headers)
    intent = client.post("/api/payments/create-intent", headers=headers, json={"order_id": order_id}).json()

    response = client.get(f"/api/payments/{intent['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == intent["id"]
