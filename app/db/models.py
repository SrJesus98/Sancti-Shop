"""Database models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    rol: str = Field(default="user")  # user or admin
    scopes: list[str] = Field(
        default_factory=lambda: ["user:read"],
        sa_column=Column(JSON, nullable=False),
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    cart_items: list["CartItem"] = Relationship(back_populates="user")
    orders: list["Order"] = Relationship(back_populates="user")
    payment_intents: list["PaymentIntent"] = Relationship(back_populates="user")


class Product(SQLModel, table=True):
    """Product model."""

    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    category: Optional[str] = Field(default=None, index=True)
    image_url: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    cart_items: list["CartItem"] = Relationship(back_populates="product")
    order_items: list["OrderItem"] = Relationship(back_populates="product")


class CartItem(SQLModel, table=True):
    """Cart item model."""

    __tablename__ = "cart_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship(back_populates="cart_items")
    product: Product = Relationship(back_populates="cart_items")


class Order(SQLModel, table=True):
    """Order model."""

    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    status: str = Field(default="En proceso")  # En proceso, Pagada, Lista, Entregada
    total: float = Field(ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: User = Relationship(back_populates="orders")
    items: list["OrderItem"] = Relationship(back_populates="order")
    payment_intents: list["PaymentIntent"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    """Order item model."""

    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(default=1, ge=1)
    price: float = Field(ge=0)  # Price at time of purchase

    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="order_items")


class PaymentIntent(SQLModel, table=True):
    """Payment intent model."""

    __tablename__ = "payment_intents"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    provider: str = Field(default="mock")
    status: str = Field(default="pending")
    simulate: Optional[str] = Field(default=None)
    redirect_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

    order: Order = Relationship(back_populates="payment_intents")
    user: User = Relationship(back_populates="payment_intents")


class PaymentWebhookEvent(SQLModel, table=True):
    """Processed webhook events for idempotency."""

    __tablename__ = "payment_webhook_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_key: str = Field(unique=True, index=True)
    payment_id: int = Field(index=True)
    order_id: int = Field(index=True)
    status: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
