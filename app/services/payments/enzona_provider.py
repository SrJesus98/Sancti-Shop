"""Enzona provider stub for future integration."""

from app.core.config import settings
from app.services.payments.adapter import CreateIntentResult, PaymentProviderAdapter


class EnzonaPaymentProvider(PaymentProviderAdapter):
    """Base/stub implementation without external calls yet."""

    def create_intent(self, payment_id: int, order_id: int, simulate: str | None = None) -> CreateIntentResult:
        return CreateIntentResult(
            status="pending",
            redirect_url=(
                f"https://enzona.local/{settings.PAYMENT_MODE}/checkout"
                f"?payment_id={payment_id}&order_id={order_id}"
            ),
        )

    def is_valid_webhook_signature(self, signature: str | None) -> bool:
        return signature == settings.PAYMENT_WEBHOOK_SECRET
