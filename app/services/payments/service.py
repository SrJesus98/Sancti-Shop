"""Payment service orchestration — ASYNC."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Order, PaymentIntent, PaymentWebhookEvent, User
from app.schemas.payments import (
    PaymentIntentCreateRequest,
    PaymentIntentResponse,
    PaymentWebhookRequest,
)
from app.services.payments.adapter import PaymentProviderAdapter
from app.services.payments.enzona_provider import EnzonaPaymentProvider
from app.services.payments.mock_provider import MockPaymentProvider


def _get_provider() -> PaymentProviderAdapter:
    """Get payment provider based on config (sync, no I/O)."""
    if settings.PAYMENT_PROVIDER == "enzona":
        return EnzonaPaymentProvider()
    return MockPaymentProvider()


async def create_payment_intent(
    session: AsyncSession,
    current_user: User,
    payload: PaymentIntentCreateRequest,
) -> PaymentIntentResponse:
    """Create a payment intent for an order."""
    result = await session.execute(select(Order).where(Order.id == payload.order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    can_access = order.user_id == current_user.id 
    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    intent = PaymentIntent(
        order_id=order.id,
        user_id=order.user_id,
        provider=settings.PAYMENT_PROVIDER,
        status="pending",
        simulate=payload.simulate,
        redirect_url="pending",
    )
    session.add(intent)
    await session.flush()

    provider = _get_provider()
    provider_result = provider.create_intent(
        payment_id=intent.id,
        order_id=order.id,
        simulate=payload.simulate,
    )
    intent.status = provider_result.status
    intent.redirect_url = provider_result.redirect_url
    intent.updated_at = datetime.utcnow()
    session.add(intent)
    await session.commit()
    await session.refresh(intent)
    return PaymentIntentResponse.model_validate(intent)


async def process_webhook(
    session: AsyncSession,
    payload: PaymentWebhookRequest,
    signature: str | None,
) -> PaymentIntentResponse:
    """Handle payment webhook events with signature + idempotency."""
    provider = _get_provider()
    if not provider.is_valid_webhook_signature(signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    event_key = f"{payload.payment_id}:{payload.order_id}:{payload.status}"
    result = await session.execute(
        select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_key == event_key)
    )
    existing_event = result.scalar_one_or_none()
    if existing_event:
        result = await session.execute(
            select(PaymentIntent).where(PaymentIntent.id == payload.payment_id)
        )
        intent = result.scalar_one_or_none()
        if not intent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        return PaymentIntentResponse.model_validate(intent)

    result = await session.execute(
        select(PaymentIntent).where(PaymentIntent.id == payload.payment_id)
    )
    intent = result.scalar_one_or_none()
    if not intent or intent.order_id != payload.order_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    result = await session.execute(select(Order).where(Order.id == payload.order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    intent.status = payload.status
    intent.updated_at = datetime.utcnow()

    if payload.status == "approved" and order.status == "En proceso":
        order.status = "Pagada"
        order.updated_at = datetime.utcnow()
        session.add(order)

    event = PaymentWebhookEvent(
        event_key=event_key,
        payment_id=payload.payment_id,
        order_id=payload.order_id,
        status=payload.status,
    )
    session.add(event)
    session.add(intent)
    await session.commit()
    await session.refresh(intent)
    return PaymentIntentResponse.model_validate(intent)


async def get_payment_intent(
    session: AsyncSession,
    payment_id: int,
    current_user: User,
) -> PaymentIntentResponse:
    """Get payment intent status."""
    result = await session.execute(
        select(PaymentIntent).where(PaymentIntent.id == payment_id)
    )
    intent = result.scalar_one_or_none()
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    can_access = intent.user_id == current_user.id 
    if not can_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return PaymentIntentResponse.model_validate(intent)