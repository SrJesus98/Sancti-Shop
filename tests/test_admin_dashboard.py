"""Tests for the admin dashboard feature (metrics service, API endpoint and view page)."""

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session

from app.core.limiter import reset_rate_limiter
from app.db.models import Order, Product, User
from app.db.session import sync_engine as engine
from app.main import app


def reset_db() -> None:
    """Reset database tables and rate limiter for test isolation."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    reset_rate_limiter()


def _register_and_login(
    client: TestClient,
    email: str,
    as_admin: bool = False,
    scopes: list[str] | None = None,
) -> dict[str, str]:
    password = "Password123!"
    client.post("/api/auth/register", json={"email": email, "password": password})

    if as_admin:
        with Session(engine) as session:
            user = session.query(User).filter(User.email == email).first()
            assert user is not None
            user.rol = "admin"
            user.scopes = scopes or ["user:read", "admin:products", "admin:orders", "admin:users"]
            session.add(user)
            session.commit()

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_user_id(email: str) -> int:
    with Session(engine) as session:
        user = session.query(User).filter(User.email == email).first()
        assert user is not None
        return user.id


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


def _seed_order(user_id: int, status: str, total: float) -> Order:
    with Session(engine) as session:
        order = Order(user_id=user_id, status=status, total=total)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order


# ==================== SERVICE / ENDPOINT: GET /api/admin/metrics ====================


def test_metrics_endpoint_sin_auth_retorna_401() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/api/admin/metrics")

    assert response.status_code == 401


def test_metrics_endpoint_usuario_normal_retorna_403() -> None:
    reset_db()
    client = TestClient(app)
    headers = _register_and_login(client, "normal-metrics@test.com")

    response = client.get("/api/admin/metrics", headers=headers)

    assert response.status_code == 403


def test_metrics_endpoint_admin_sin_scope_admin_users_retorna_403() -> None:
    reset_db()
    client = TestClient(app)
    # Admin role but missing the specific "admin:users" scope required by this endpoint.
    headers = _register_and_login(
        client,
        "admin-no-scope@test.com",
        as_admin=True,
        scopes=["user:read", "admin:orders", "admin:products"],
    )

    response = client.get("/api/admin/metrics", headers=headers)

    assert response.status_code == 403


def test_metrics_endpoint_admin_con_scope_retorna_metricas_correctas() -> None:
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-metrics@test.com", as_admin=True)
    admin_id = _get_user_id("admin-metrics@test.com")

    _seed_product(name="Activo1", is_active=True)
    _seed_product(name="Activo2", is_active=True)
    _seed_product(name="Inactivo", is_active=False)

    _seed_order(admin_id, status="Pagada", total=100.0)
    _seed_order(admin_id, status="En proceso", total=50.0)
    _seed_order(admin_id, status="Entregada", total=75.5)

    response = client.get("/api/admin/metrics", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_users"] == 1
    assert body["total_products"] == 2
    assert body["total_orders"] == 3
    assert body["orders_by_status"] == {"Pagada": 1, "En proceso": 1, "Entregada": 1}
    assert body["total_revenue"] == 175.5


def test_metrics_endpoint_sin_datos_retorna_ceros() -> None:
    reset_db()
    client = TestClient(app)
    admin_headers = _register_and_login(client, "admin-empty@test.com", as_admin=True)

    response = client.get("/api/admin/metrics", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_users"] == 1
    assert body["total_products"] == 0
    assert body["total_orders"] == 0
    assert body["orders_by_status"] == {}
    assert body["total_revenue"] == 0


# ==================== VIEW PAGE: GET /views/admin/dashboard ====================


def test_dashboard_page_no_autenticado_redirige_a_login() -> None:
    reset_db()
    client = TestClient(app)

    response = client.get("/views/admin/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/views/login"


def test_dashboard_page_usuario_normal_redirige_a_home() -> None:
    reset_db()
    client = TestClient(app)
    _register_and_login(client, "normal-dashboard-page@test.com")

    response = client.get("/views/admin/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/views/"


def test_dashboard_page_admin_renderiza_metricas() -> None:
    reset_db()
    client = TestClient(app)
    _register_and_login(client, "admin-dashboard-page@test.com", as_admin=True)
    admin_id = _get_user_id("admin-dashboard-page@test.com")

    _seed_product(name="P1", is_active=True)
    _seed_order(admin_id, status="Pagada", total=100.0)
    _seed_order(admin_id, status="Entregada", total=75.5)

    response = client.get("/views/admin/dashboard")

    assert response.status_code == 200
    assert "Órdenes por Estado" in response.text
    assert "$175.50" in response.text
    assert "Pagada" in response.text
    assert "Entregada" in response.text


# ==================== NAVBAR: Dashboard link visibility ====================


def test_navbar_muestra_link_dashboard_para_admin() -> None:
    reset_db()
    client = TestClient(app)
    _register_and_login(client, "admin-navbar@test.com", as_admin=True)

    response = client.get("/views/")

    assert response.status_code == 200
    assert '/views/admin/dashboard' in response.text
    assert "📊 Dashboard" in response.text


def test_navbar_no_muestra_link_dashboard_para_usuario_normal() -> None:
    reset_db()
    client = TestClient(app)
    _register_and_login(client, "normal-navbar@test.com")

    response = client.get("/views/")

    assert response.status_code == 200
    assert '/views/admin/dashboard' not in response.text