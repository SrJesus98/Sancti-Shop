"""Payment API endpoints — ASYNC."""

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.limiter import limiter
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.payments import PaymentIntentCreateRequest, PaymentIntentResponse, PaymentWebhookRequest
from app.services.payments.service import create_payment_intent, get_payment_intent, process_webhook


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_intent_endpoint(
    request: Request,
    payload: PaymentIntentCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> PaymentIntentResponse:
    """Create a payment intent for an order."""
    return await create_payment_intent(session, current_user, payload)


@router.post("/webhook", response_model=PaymentIntentResponse)
@limiter.limit("10/minute")
async def webhook_endpoint(
    request: Request,
    payload: PaymentWebhookRequest,
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    session: AsyncSession = Depends(get_async_session),
) -> PaymentIntentResponse:
    """Handle payment webhook events with signature + idempotency."""
    return await process_webhook(session, payload, x_webhook_signature)


@router.get("/{payment_id}", response_model=PaymentIntentResponse)
async def get_payment_endpoint(
    payment_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> PaymentIntentResponse:
    """Get payment intent status."""
    return await get_payment_intent(session, payment_id, current_user)