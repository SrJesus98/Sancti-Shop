"""Phase 2 product tests (admin CRUD + public listing)."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.core.limiter import reset_rate_limiter
from app.db.models import Product, User
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
            user.scopes = ["user:read", "admin:products"]
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


def test_usuario_normal_no_puede_crear_editar_eliminar_producto() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "normal@test.com", as_admin=False)
    seeded = _seed_product(name="Seeded")

    create_res = client.post(
        "/api/products",
        headers=headers,
        json={
            "name": "New Product",
            "description": "Desc",
            "price": 99.0,
            "stock": 4,
            "category": "tech",
            "is_active": True,
        },
    )
    assert create_res.status_code == 403

    update_res = client.put(
        f"/api/products/{seeded.id}",
        headers=headers,
        json={
            "name": "Updated",
            "description": "Updated desc",
            "price": 109.0,
            "stock": 6,
            "category": "tech",
            "is_active": True,
        },
    )
    assert update_res.status_code == 403

    delete_res = client.delete(f"/api/products/{seeded.id}", headers=headers)
    assert delete_res.status_code == 403


def test_admin_si_puede_crear_editar_eliminar_producto() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "admin@test.com", as_admin=True)

    create_res = client.post(
        "/api/products",
        headers=headers,
        json={
            "name": "Gaming Mouse",
            "description": "RGB",
            "price": 59.9,
            "stock": 10,
            "category": "perifericos",
            "is_active": True,
        },
    )
    assert create_res.status_code == 201
    product_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/products/{product_id}",
        headers=headers,
        json={
            "name": "Gaming Mouse Pro",
            "description": "RGB + DPI",
            "price": 79.9,
            "stock": 8,
            "category": "perifericos",
            "is_active": True,
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Gaming Mouse Pro"

    delete_res = client.delete(f"/api/products/{product_id}", headers=headers)
    assert delete_res.status_code == 204


def test_listado_publico_paginado_funciona() -> None:
    reset_db()
    client = TestClient(app)
    _seed_product(name="P1", category="c1")
    _seed_product(name="P2", category="c1")
    _seed_product(name="P3", category="c2")

    page_1 = client.get("/api/products?page=1&size=2")
    assert page_1.status_code == 200
    body_1 = page_1.json()
    assert body_1["page"] == 1
    assert body_1["size"] == 2
    assert body_1["total"] == 3
    assert len(body_1["items"]) == 2

    page_2 = client.get("/api/products?page=2&size=2")
    assert page_2.status_code == 200
    body_2 = page_2.json()
    assert body_2["page"] == 2
    assert len(body_2["items"]) == 1


def test_filtro_por_categoria_funciona() -> None:
    reset_db()
    client = TestClient(app)
    _seed_product(name="Book A", category="books")
    _seed_product(name="Book B", category="books")
    _seed_product(name="Keyboard", category="tech")

    response = client.get("/api/products?category=books")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert {item["category"] for item in body["items"]} == {"books"}


def test_producto_inactivo_o_sin_stock_no_aparece_en_listado_publico() -> None:
    reset_db()
    client = TestClient(app)
    _seed_product(name="Visible", is_active=True, stock=10)
    _seed_product(name="Inactive", is_active=False, stock=10)
    _seed_product(name="NoStock", is_active=True, stock=0)

    response = client.get("/api/products")
    assert response.status_code == 200
    items = response.json()["items"]
    names = {item["name"] for item in items}
    assert names == {"Visible"}
