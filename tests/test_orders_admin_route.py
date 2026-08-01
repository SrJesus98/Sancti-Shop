"""Tests for the /api/orders admin route change and the eager-loaded order response."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.core.limiter import reset_rate_limiter
from app.db.models import User
from app.db.session import sync_engine as engine
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


def _seed_product(client: TestClient, admin_headers: dict[str, str], **kwargs) -> dict:
    payload = {
        "name": "Default Product",
        "description": "Desc",
        "price": 10.0,
        "stock": 5,
        "category": "general",
        "is_active": True,
    }
    payload.update(kwargs)
    response = client.post("/api/products", headers=admin_headers, json=payload)
    assert response.status_code == 201
    return response.json()


# ==================== ROUTE: GET /api/orders/admin ====================


def test_admin_orders_route_sin_auth_retorna_401() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/api/orders/admin")

    assert response.status_code == 401


def test_admin_orders_route_usuario_normal_retorna_403() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "normal-admin-orders@test.com")

    response = client.get("/api/orders/admin", headers=headers)

    assert response.status_code == 403


def test_admin_orders_route_no_es_capturada_por_ruta_order_id() -> None:
    """Regression test: '/admin' must resolve to the admin listing route and not be
    swallowed by the '/{order_id}' route (which would try to parse 'admin' as an int
    and return 422 instead of the intended admin listing).
    """
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-route-order@test.com", as_admin=True)

    response = client.get("/api/orders/admin", headers=admin_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_orders_route_devuelve_todas_las_ordenes() -> None:
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-route-list@test.com", as_admin=True)
    user_headers = _register_and_login(client, "buyer-route-list@test.com")
    product = _seed_product(client, admin_headers, name="Router Product", price=15.0, stock=10)

    client.post(
        "/api/cart/items",
        headers=user_headers,
        json={"product_id": product["id"], "quantity": 2},
    )
    checkout = client.post("/api/orders", headers=user_headers)
    assert checkout.status_code == 201

    response = client.get("/api/orders/admin", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["total"] == 30.0


def test_admin_orders_all_suffix_ya_no_existe() -> None:
    """The '/admin/all' path used previously must no longer resolve."""
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-old-path@test.com", as_admin=True)

    response = client.get("/api/orders/admin/all", headers=admin_headers)

    assert response.status_code == 404


# ==================== SERVICE: create_order_from_cart eager loading ====================


def test_create_order_incluye_product_name_y_user_email() -> None:
    """Regression test: after refactoring create_order_from_cart to re-query the order
    with selectinload (instead of session.refresh), the response must include the
    product name and user email without lazy-loading errors."""
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-create-order@test.com", as_admin=True)
    user_headers = _register_and_login(client, "buyer-create-order@test.com")
    product = _seed_product(client, admin_headers, name="Eager Load Product", price=25.0, stock=10)

    client.post(
        "/api/cart/items",
        headers=user_headers,
        json={"product_id": product["id"], "quantity": 3},
    )

    response = client.post("/api/orders", headers=user_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "En proceso"
    assert body["total"] == 75.0
    assert body["user_email"] == "buyer-create-order@test.com"
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["product_id"] == product["id"]
    assert item["product_name"] == "Eager Load Product"
    assert item["quantity"] == 3


def test_create_order_multiples_items_incluyen_su_propio_producto() -> None:
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-multi-order@test.com", as_admin=True)
    user_headers = _register_and_login(client, "buyer-multi-order@test.com")
    p1 = _seed_product(client, admin_headers, name="Alpha", price=10.0, stock=5)
    p2 = _seed_product(client, admin_headers, name="Beta", price=20.0, stock=5)

    client.post("/api/cart/items", headers=user_headers, json={"product_id": p1["id"], "quantity": 1})
    client.post("/api/cart/items", headers=user_headers, json={"product_id": p2["id"], "quantity": 2})

    response = client.post("/api/orders", headers=user_headers)

    assert response.status_code == 201
    body = response.json()
    names = {item["product_id"]: item["product_name"] for item in body["items"]}
    assert names[p1["id"]] == "Alpha"
    assert names[p2["id"]] == "Beta"