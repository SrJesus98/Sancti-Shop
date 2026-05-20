"""Phase 4 orders/checkout tests (TDD)."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.core.limiter import reset_rate_limiter
from app.db.models import CartItem, Order, OrderItem, Product, User
from app.db.session import engine
from app.main import app


def reset_db() -> None:
    """Reset database tables and rate limiter for test isolation."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    reset_rate_limiter()


def _register_and_login(client: TestClient, email: str, as_admin: bool = False) -> dict[str, str]:
    password = "Password123!"
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


def _seed_product(**kwargs) -> Product:
    payload = {
        "name": "Default Product",
        "description": "Desc",
        "price": 10.0,
        "stock": 5,
        "category": "general",
        "is_active": True,
    }
    payload.update(kwargs)

    with Session(engine) as session:
        product = Product(**payload)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product


def test_checkout_desde_carrito_crea_orden_items_y_limpia_carrito() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "checkout@test.com")
    p1 = _seed_product(name="Mouse", price=20.0, stock=10)
    p2 = _seed_product(name="Keyboard", price=30.0, stock=10)

    client.post("/api/cart/items", headers=headers, json={"product_id": p1.id, "quantity": 2})
    client.post("/api/cart/items", headers=headers, json={"product_id": p2.id, "quantity": 1})

    response = client.post("/api/orders/checkout", headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "En proceso"
    assert body["total"] == 70.0
    assert len(body["items"]) == 2

    with Session(engine) as session:
        orders = session.query(Order).all()
        order_items = session.query(OrderItem).all()
        cart_items = session.query(CartItem).all()
        assert len(orders) == 1
        assert len(order_items) == 2
        assert len(cart_items) == 0


def test_checkout_descuenta_stock_correctamente() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "stock-checkout@test.com")
    p = _seed_product(name="SSD", stock=5, price=50.0)

    client.post("/api/cart/items", headers=headers, json={"product_id": p.id, "quantity": 3})
    response = client.post("/api/orders/checkout", headers=headers)
    assert response.status_code == 201

    with Session(engine) as session:
        updated = session.query(Product).filter(Product.id == p.id).first()
        assert updated is not None
        assert updated.stock == 2


def test_historial_devuelve_pedidos_del_usuario_autenticado() -> None:
    reset_db()
    client = TestClient(app)
    headers_a = _register_and_login(client, "user-a@test.com")
    headers_b = _register_and_login(client, "user-b@test.com")
    p = _seed_product(name="Cable", stock=10, price=5.0)

    client.post("/api/cart/items", headers=headers_a, json={"product_id": p.id, "quantity": 2})
    client.post("/api/orders/checkout", headers=headers_a)

    client.post("/api/cart/items", headers=headers_b, json={"product_id": p.id, "quantity": 1})
    client.post("/api/orders/checkout", headers=headers_b)

    response = client.get("/api/orders", headers=headers_a)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["total"] == 10.0


def test_endpoints_orders_protegidos_sin_auth_retorna_401() -> None:
    reset_db()
    client = TestClient(app)

    assert client.get("/api/orders").status_code == 401
    assert client.post("/api/orders/checkout").status_code == 401
    assert client.patch("/api/orders/1/pay").status_code == 401


def test_transiciones_invalidas_retorna_409() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "invalid-transition@test.com")
    admin_headers = _register_and_login(client, "admin-transition@test.com", as_admin=True)
    p = _seed_product(name="Webcam", stock=4, price=25.0)

    client.post("/api/cart/items", headers=headers, json={"product_id": p.id, "quantity": 1})
    checkout = client.post("/api/orders/checkout", headers=headers)
    order_id = checkout.json()["id"]

    invalid_admin = client.patch(f"/api/orders/{order_id}/status", headers=admin_headers, json={"status": "Lista"})
    assert invalid_admin.status_code == 409


def test_admin_puede_mover_pagada_a_lista_a_entregada() -> None:
    reset_db()
    client = TestClient(app)
    user_headers = _register_and_login(client, "user-state@test.com")
    admin_headers = _register_and_login(client, "admin-state@test.com", as_admin=True)
    p = _seed_product(name="Monitor", stock=3, price=200.0)

    client.post("/api/cart/items", headers=user_headers, json={"product_id": p.id, "quantity": 1})
    checkout = client.post("/api/orders/checkout", headers=user_headers)
    order_id = checkout.json()["id"]

    pay_response = client.patch(f"/api/orders/{order_id}/pay", headers=user_headers)
    assert pay_response.status_code == 200
    assert pay_response.json()["status"] == "Pagada"

    ready_response = client.patch(
        f"/api/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "Lista"},
    )
    assert ready_response.status_code == 200
    assert ready_response.json()["status"] == "Lista"

    delivered_response = client.patch(
        f"/api/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "Entregada"},
    )
    assert delivered_response.status_code == 200
    assert delivered_response.json()["status"] == "Entregada"


def test_usuario_normal_no_puede_endpoint_admin_orders() -> None:
    reset_db()
    client = TestClient(app)
    user_headers = _register_and_login(client, "user-no-admin@test.com")
    p = _seed_product(name="Speaker", stock=2, price=40.0)

    client.post("/api/cart/items", headers=user_headers, json={"product_id": p.id, "quantity": 1})
    checkout = client.post("/api/orders/checkout", headers=user_headers)
    order_id = checkout.json()["id"]
    client.patch(f"/api/orders/{order_id}/pay", headers=user_headers)

    response = client.patch(
        f"/api/orders/{order_id}/status",
        headers=user_headers,
        json={"status": "Lista"},
    )
    assert response.status_code == 403
