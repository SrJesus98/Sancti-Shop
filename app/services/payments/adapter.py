"""Payment provider adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CreateIntentResult:
    """Provider response for creating payment intent."""

    status: str
    redirect_url: str


class PaymentProviderAdapter(ABC):
    """Contract every payment provider must implement."""

    @abstractmethod
    def create_intent(self, payment_id: int, order_id: int, simulate: str | None = None) -> CreateIntentResult:
        """Create provider-side intent."""

    @abstractmethod
    def is_valid_webhook_signature(self, signature: str | None) -> bool:
        """Validate webhook signature."""
