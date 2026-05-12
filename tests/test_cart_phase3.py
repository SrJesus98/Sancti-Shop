"""Phase 3 cart tests (TDD)."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.db.models import Product
from app.db.session import engine
from app.main import app


def reset_db() -> None:
    """Reset database tables for test isolation."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _register_and_login(client: TestClient, email: str) -> dict[str, str]:
    password = "password123"
    client.post("/api/auth/register", json={"email": email, "password": password})
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


def test_agregar_item_nuevo_al_carrito() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "cart-new@test.com")
    product = _seed_product(name="Mouse", price=20.0)

    response = client.post(
        "/api/cart/items",
        headers=headers,
        json={"product_id": product.id, "quantity": 2},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["product_id"] == product.id
    assert body["items"][0]["quantity"] == 2


def test_agregar_mismo_producto_incrementa_cantidad() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "cart-inc@test.com")
    product = _seed_product(name="Keyboard", price=30.0)

    first = client.post(
        "/api/cart/items",
        headers=headers,
        json={"product_id": product.id, "quantity": 1},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/cart/items",
        headers=headers,
        json={"product_id": product.id, "quantity": 3},
    )
    assert second.status_code == 201
    body = second.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 4


def test_ver_carrito_devuelve_subtotales_correctos() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "cart-view@test.com")
    p1 = _seed_product(name="A", price=10.0)
    p2 = _seed_product(name="B", price=7.5)

    client.post("/api/cart/items", headers=headers, json={"product_id": p1.id, "quantity": 2})
    client.post("/api/cart/items", headers=headers, json={"product_id": p2.id, "quantity": 4})

    response = client.get("/api/cart", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    subtotals = {item["product_id"]: item["subtotal"] for item in body["items"]}
    assert subtotals[p1.id] == 20.0
    assert subtotals[p2.id] == 30.0
    assert body["total"] == 50.0


def test_actualizar_cantidad_a_cero_elimina_item() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "cart-update@test.com")
    product = _seed_product(name="Stand", price=15.0)

    add = client.post(
        "/api/cart/items",
        headers=headers,
        json={"product_id": product.id, "quantity": 2},
    )
    cart_item_id = add.json()["items"][0]["id"]

    update = client.put(
        f"/api/cart/items/{cart_item_id}",
        headers=headers,
        json={"quantity": 0},
    )
    assert update.status_code == 200
    assert update.json()["items"] == []


def test_vaciar_carrito_elimina_todos_los_items() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "cart-clear@test.com")
    p1 = _seed_product(name="Cable")
    p2 = _seed_product(name="Adapter")

    client.post("/api/cart/items", headers=headers, json={"product_id": p1.id, "quantity": 1})
    client.post("/api/cart/items", headers=headers, json={"product_id": p2.id, "quantity": 2})

    clear_response = client.delete("/api/cart", headers=headers)
    assert clear_response.status_code == 200
    assert clear_response.json()["items"] == []
    assert clear_response.json()["total"] == 0.0


def test_agregar_producto_inactivo_o_sin_stock_retorna_error_claro() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "cart-stock@test.com")
    inactive = _seed_product(name="Inactive", is_active=False, stock=5)
    no_stock = _seed_product(name="NoStock", is_active=True, stock=0)

    inactive_response = client.post(
        "/api/cart/items",
        headers=headers,
        json={"product_id": inactive.id, "quantity": 1},
    )
    assert inactive_response.status_code in (400, 409)
    assert "inactive" in inactive_response.json()["detail"].lower()

    no_stock_response = client.post(
        "/api/cart/items",
        headers=headers,
        json={"product_id": no_stock.id, "quantity": 1},
    )
    assert no_stock_response.status_code in (400, 409)
    assert "stock" in no_stock_response.json()["detail"].lower()


def test_endpoints_carrito_sin_auth_retorna_401() -> None:
    reset_db()
    client = TestClient(app)
    product = _seed_product(name="NoAuth", stock=2)

    assert client.get("/api/cart").status_code == 401
    assert client.delete("/api/cart").status_code == 401
    assert (
        client.post("/api/cart/items", json={"product_id": product.id, "quantity": 1}).status_code
        == 401
    )
    assert client.put("/api/cart/items/1", json={"quantity": 2}).status_code == 401
