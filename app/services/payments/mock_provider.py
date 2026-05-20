"""Mock payment provider implementation."""

from app.core.config import settings
from app.services.payments.adapter import CreateIntentResult, PaymentProviderAdapter


class MockPaymentProvider(PaymentProviderAdapter):
    """Mock provider for local/sandbox flows."""

    def create_intent(self, payment_id: int, order_id: int, simulate: str | None = None) -> CreateIntentResult:
        """Mock: devuelve 'pending' para que el frontend simule el webhook localmente."""
        return CreateIntentResult(
            status="pending",
            redirect_url="pending",
        )

    def is_valid_webhook_signature(self, signature: str | None) -> bool:
        return signature == settings.PAYMENT_WEBHOOK_SECRET
