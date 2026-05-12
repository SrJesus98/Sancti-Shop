"""Payment request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PaymentIntentCreateRequest(BaseModel):
    """Create payment intent payload."""

    order_id: int
    simulate: Literal["approved", "rejected", "timeout"] | None = None


class PaymentWebhookRequest(BaseModel):
    """Webhook event payload."""

    payment_id: int
    order_id: int
    status: Literal["approved", "rejected", "timeout", "pending"]


class PaymentIntentResponse(BaseModel):
    """Payment intent response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    provider: str
    status: str
    simulate: str | None = None
    redirect_url: str
    created_at: datetime
    updated_at: datetime | None = None
