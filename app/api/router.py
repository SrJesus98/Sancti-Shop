"""Main API router."""

from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.cart import router as cart_router
from app.api.endpoints.orders import router as orders_router
from app.api.endpoints.payments import router as payments_router
from app.api.endpoints.products import router as products_router


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
