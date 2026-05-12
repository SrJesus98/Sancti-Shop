"""Mock payment provider implementation."""

from app.core.config import settings
from app.services.payments.adapter import CreateIntentResult, PaymentProviderAdapter


class MockPaymentProvider(PaymentProviderAdapter):
    """Mock provider for local/sandbox flows."""

    def create_intent(self, payment_id: int, order_id: int, simulate: str | None = None) -> CreateIntentResult:
        return CreateIntentResult(
            status="pending",
            redirect_url=(
                f"https://mock-payments.local/checkout?payment_id={payment_id}"
                f"&order_id={order_id}&simulate={simulate or 'approved'}"
            ),
        )

    def is_valid_webhook_signature(self, signature: str | None) -> bool:
        return signature == settings.PAYMENT_WEBHOOK_SECRET
