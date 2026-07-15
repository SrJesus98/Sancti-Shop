"""View routes that render HTML pages with Jinja2 — ASYNC version."""

from fastapi import APIRouter, Cookie, Depends, Request, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.models import CartItem, Order, Product, User
from app.db.session import get_async_session
from app.services.dashboard import get_dashboard_metrics

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/views", tags=["views"])


# ==================== USER DEPENDENCY ====================

async def get_optional_user(
    cookie_token: str | None = Cookie(default=None, alias="access_token"),
    session: AsyncSession = Depends(get_async_session),
) -> User | None:
    """Return authenticated user or None (no error raised)."""
    if not cookie_token:
        return None
    payload = decode_token(cookie_token)
    if not payload or "sub" not in payload:
        return None
    result = await session.execute(select(User).where(User.email == payload["sub"]))
    user = result.scalar_one_or_none()
    return user


async def require_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    """Require authenticated user, redirect to login if not."""
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/views/login"})
    return user


async def require_admin(
    user: User = Depends(require_user),
) -> User:
    """Require admin user."""
    if user.rol != "admin":
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/views/"})
    return user


# ==================== CONTEXT HELPER ====================

async def _context(user: User | None, session: AsyncSession, extra: dict | None = None) -> dict:
    """Build base template context with user info and real cart count."""
    ctx = {
        "user": user,
        "cart_count": 0,
    }
    if user:
        result = await session.execute(
            select(func.count()).select_from(CartItem).where(CartItem.user_id == user.id)
        )
        ctx["cart_count"] = result.scalar() or 0
    if extra:
        ctx.update(extra)
    return ctx


# ==================== ROUTES ====================

@router.get("/")
async def home(
    request: Request,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Home page — public product catalog."""
    result = await session.execute(
        select(Product).where(Product.is_active == True)
    )
    products = result.scalars().all()

    cat_result = await session.execute(
        select(Product.category).where(Product.is_active == True).distinct()
    )
    categories = [row[0] for row in cat_result if row[0]]

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
        await _context(user, session, {
            "products": products,
            "products_json": products_json,
            "categories": categories,
        })
    )


@router.get("/login")
async def login_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Login page."""
    if user:
        return RedirectResponse(url="/views/")
    return templates.TemplateResponse(
        request,
        "pages/login.html",
        await _context(user, session)
    )


@router.get("/register")
async def register_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Register page."""
    if user:
        return RedirectResponse(url="/views/")
    return templates.TemplateResponse(
        request,
        "pages/register.html",
        await _context(user, session)
    )


@router.get("/cart")
async def cart_page(
    request: Request,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Cart page."""
    return templates.TemplateResponse(
        request,
        "pages/cart.html",
        await _context(user, session)
    )


@router.get("/product/{product_id}")
async def product_detail(
    request: Request,
    product_id: int,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Product detail page."""
    result = await session.execute(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return templates.TemplateResponse(
        request,
        "pages/product_detail.html",
        await _context(user, session, {"product": product})
    )


@router.get("/checkout")
async def checkout_page(
    request: Request,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Checkout page (requires login)."""
    return templates.TemplateResponse(
        request,
        "pages/checkout.html",
        await _context(user, session)
    )


@router.get("/profile")
async def profile_page(
    request: Request,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_async_session),
):
    """User profile page."""
    return templates.TemplateResponse(
        request,
        "pages/profile.html",
        await _context(user, session)
    )


@router.get("/orders")
async def orders_page(
    request: Request,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_async_session),
):
    """User orders history page."""
    return templates.TemplateResponse(
        request,
        "pages/orders.html",
        await _context(user, session)
    )


# ==================== ADMIN ROUTES ====================

@router.get("/admin/products")
async def admin_products(
    request: Request,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Admin product management page."""
    result = await session.execute(select(Product))
    products = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "pages/admin/products.html",
        await _context(user, session, {"products": products})
    )


@router.get("/admin/products/new")
async def admin_product_new(
    request: Request,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Admin product creation form."""
    cat_result = await session.execute(
        select(Product.category).where(Product.category.isnot(None)).distinct()
    )
    categories = [row[0] for row in cat_result if row[0]]

    return templates.TemplateResponse(
        request,
        "pages/admin/product_form.html",
        {
            "request": request,
            "user": user,
            "product": None,
            "categories": categories,
            "is_edit": False,
        }
    )


@router.get("/admin/products/{product_id}")
async def admin_product_edit(
    product_id: int,
    request: Request,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Admin product edit form."""
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    cat_result = await session.execute(
        select(Product.category).where(Product.category.isnot(None)).distinct()
    )
    categories = [row[0] for row in cat_result if row[0]]

    return templates.TemplateResponse(
        request,
        "pages/admin/product_form.html",
        {
            "request": request,
            "user": user,
            "product": product,
            "categories": categories,
            "is_edit": True,
        }
    )


@router.get("/admin/orders")
async def admin_orders(
    request: Request,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Admin order management page."""
    return templates.TemplateResponse(
        request,
        "pages/admin/orders.html",
        await _context(user, session)
    )


@router.get("/admin/users")
async def admin_users(
    request: Request,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Admin user management page."""
    return templates.TemplateResponse(
        request,
        "pages/admin/users.html",
        await _context(user, session)
    )

@router.get("/admin/dashboard")
async def admin_dashboard_page(
    request: Request,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """Admin dashboard page with metrics."""
    metrics = await get_dashboard_metrics(session)
    return templates.TemplateResponse(
        request,
        "pages/admin/dashboard.html",
        await _context(user, session, {"metrics": metrics})
    )
