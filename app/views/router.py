"""View routes that render HTML pages with Jinja2."""

from fastapi import APIRouter, Cookie, Depends, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.security import decode_token
from app.db.models import Order, Product, User
from app.db.session import get_session

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/views", tags=["views"])


# ==================== USER DEPENDENCY ====================

def get_optional_user(
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    session: Session = Depends(get_session),
) -> User | None:
    """Return authenticated user or None (no error raised)."""
    if not cookie_token:
        return None
    payload = decode_token(cookie_token)
    if not payload or "sub" not in payload:
        return None
    user = session.query(User).filter(User.email == payload["sub"]).first()
    return user


def require_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    """Require authenticated user, redirect to login if not."""
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/views/login"})
    return user


def require_admin(
    user: User = Depends(require_user),
) -> User:
    """Require admin user."""
    if user.rol != "admin":
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/views/"})
    return user


# ==================== CONTEXT HELPER ====================

def _context(user: User | None, extra: dict | None = None) -> dict:
    """Build base template context with user info."""
    ctx = {
        "user": user,
        "cart_count": 0,  # Se calcula más adelante si hay carrito
    }
    if extra:
        ctx.update(extra)
    return ctx


# ==================== ROUTES ====================

@router.get("/")
async def home(
    request: Request,
    user: User | None = Depends(get_optional_user),
    session: Session = Depends(get_session),
):
    """Home page — public product catalog."""
    products = session.query(Product).filter(Product.is_active == True).all()
    categories = session.query(Product.category).filter(Product.is_active == True).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    # Serializar productos a dict para JS
    products_json = [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "stock": p.stock,
            "category": p.category,
            "description": p.description,
            "image_url": p.image_url,
        }
        for p in products
    ]

    return templates.TemplateResponse(
        request,
        "pages/index.html",
        _context(user, {
            "products": products,
            "products_json": products_json,
            "categories": categories,
        })
    )


@router.get("/login")
async def login_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
):
    """Login page."""
    if user:
        return RedirectResponse(url="/views/")
    return templates.TemplateResponse(
        request,
        "pages/login.html",
        _context(user)
    )


@router.get("/register")
async def register_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
):
    """Register page."""
    if user:
        return RedirectResponse(url="/views/")
    return templates.TemplateResponse(
        request,
        "pages/register.html",
        _context(user)
    )


@router.get("/cart")
async def cart_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
):
    """Cart page."""
    return templates.TemplateResponse(
        request,
        "pages/cart.html",
        _context(user)
    )


@router.get("/product/{product_id}")
async def product_detail(
    request: Request,
    product_id: int,
    user: User | None = Depends(get_optional_user),
    session: Session = Depends(get_session),
):
    """Product detail page."""
    product = session.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return templates.TemplateResponse(
        request,
        "pages/product_detail.html",
        _context(user, {"product": product})
    )


@router.get("/checkout")
async def checkout_page(
    request: Request,
    user: User = Depends(require_user),
):
    """Checkout page (requires login)."""
    return templates.TemplateResponse(
        request,
        "pages/checkout.html",
        _context(user)
    )


@router.get("/profile")
async def profile_page(
    request: Request,
    user: User = Depends(require_user),
):
    """User profile page."""
    return templates.TemplateResponse(
        request,
        "pages/profile.html",
        _context(user)
    )


@router.get("/orders")
async def orders_page(
    request: Request,
    user: User = Depends(require_user),
):
    """User orders history page."""
    return templates.TemplateResponse(
        request,
        "pages/orders.html",
        _context(user)
    )


# ==================== ADMIN ROUTES ====================

@router.get("/admin/products")
async def admin_products(
    request: Request,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Admin product management page."""
    products = session.query(Product).all()
    return templates.TemplateResponse(
        request,
        "pages/admin/products.html",
        _context(user, {"products": products})
    )


@router.get("/admin/orders")
async def admin_orders(
    request: Request,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Admin order management page."""
    return templates.TemplateResponse(
        request,
        "pages/admin/orders.html",
        _context(user)
    )


@router.get("/admin/users")
async def admin_users(
    request: Request,
    user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """Admin user management page."""
    return templates.TemplateResponse(
        request,
        "pages/admin/users.html",
        _context(user)
    )
