"""Database models."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


def utc_now_naive() -> datetime:
    """Return the current UTC time for timestamp-without-time-zone columns."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    rol: str = Field(default="user")  # user or admin
    scopes: list[str] = Field(
        default_factory=lambda: ["user:read"],
        sa_column=Column(JSON, nullable=False),
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now_naive)

    # Relationships
    cart_items: list["CartItem"] = Relationship(back_populates="user")
    orders: list["Order"] = Relationship(back_populates="user")
    payment_intents: list["PaymentIntent"] = Relationship(back_populates="user")


class Product(SQLModel, table=True):
    """Product model."""

    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    category: str | None = Field(default=None, index=True)
    image_url: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now_naive)

    # Relationships
    cart_items: list["CartItem"] = Relationship(back_populates="product")
    order_items: list["OrderItem"] = Relationship(back_populates="product")


class CartItem(SQLModel, table=True):
    """Cart item model."""

    __tablename__ = "cart_items"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now_naive)

    # Relationships
    user: User = Relationship(back_populates="cart_items")
    product: Product = Relationship(back_populates="cart_items")


class Order(SQLModel, table=True):
    """Order model."""

    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    status: str = Field(default="En proceso")  # En proceso, Pagada, Lista, Entregada
    total: float = Field(ge=0)
    created_at: datetime = Field(default_factory=utc_now_naive)
    updated_at: datetime | None = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    payment_intents: list["PaymentIntent"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """Order item model."""

    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(default=1, ge=1)
    price: float = Field(ge=0)  # Price at time of purchase

    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="order_items")


class PaymentIntent(SQLModel, table=True):
    """Payment intent model."""

    __tablename__ = "payment_intents"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    provider: str = Field(default="mock")
    status: str = Field(default="pending")
    simulate: str | None = Field(default=None)
    redirect_url: str
    created_at: datetime = Field(default_factory=utc_now_naive)
    updated_at: datetime | None = Field(default=None)

    order: Order = Relationship(back_populates="payment_intents")
    user: User = Relationship(back_populates="payment_intents")


class PaymentWebhookEvent(SQLModel, table=True):
    """Processed webhook events for idempotency."""

    __tablename__ = "payment_webhook_events"

    id: int | None = Field(default=None, primary_key=True)
    event_key: str = Field(unique=True, index=True)
    payment_id: int = Field(index=True)
    order_id: int = Field(index=True)
    status: str
    created_at: datetime = Field(default_factory=utc_now_naive)
