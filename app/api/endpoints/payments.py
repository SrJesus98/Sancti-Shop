"""Payments API endpoints."""

from fastapi import APIRouter, Depends, Header, Request, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user
from app.core.limiter import limiter
from app.db.models import User
from app.db.session import get_session
from app.schemas.payments import PaymentIntentCreateRequest, PaymentIntentResponse, PaymentWebhookRequest
from app.services.payments.service import create_payment_intent, get_payment_intent, process_webhook


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_intent_endpoint(
    request: Request,
    payload: PaymentIntentCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaymentIntentResponse:
    """Create a payment intent for an order."""
    return create_payment_intent(session, current_user, payload)


@router.post("/webhook", response_model=PaymentIntentResponse)
@limiter.limit("10/minute")
def webhook_endpoint(
    request: Request,
    payload: PaymentWebhookRequest,
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    session: Session = Depends(get_session),
) -> PaymentIntentResponse:
    """Handle payment webhook events with signature + idempotency."""
    return process_webhook(session, payload, x_webhook_signature)


@router.get("/{payment_id}", response_model=PaymentIntentResponse)
def get_payment_endpoint(
    payment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PaymentIntentResponse:
    """Get payment intent status."""
    return get_payment_intent(session, payment_id, current_user)
