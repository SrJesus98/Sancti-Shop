"""Seed database with initial data for development/testing."""

import logging

from sqlmodel import Session

from app.core.security import get_password_hash
from app.db.models import Product, User
from app.db.session import engine

logger = logging.getLogger(__name__)


def seed_database() -> None:
    """Seed users and products if the database is empty."""
    with Session(engine) as session:
        existing_users = session.query(User).count()
        if existing_users > 0:
            logger.info("Database already has %d users — skipping seed", existing_users)
            return

        logger.info("Seeding database with initial data...")

        # ── Users ──────────────────────────────────────────────
        admin = User(
            email="admin@test.com",
            hashed_password=get_password_hash("Admin123!"),
            rol="admin",
            scopes=["admin:read", "user:read"],
        )
        user = User(
            email="user@test.com",
            hashed_password=get_password_hash("User1234!"),
            rol="user",
            scopes=["user:read"],
        )
        session.add(admin)
        session.add(user)
        session.commit()
        session.refresh(admin)
        session.refresh(user)
        logger.info("  ✅ Created admin@test.com / Admin123!")
        logger.info("  ✅ Created user@test.com / User1234!")

        # ── Products ───────────────────────────────────────────
        products = [
            Product(name="Laptop Pro", description="Potente laptop para trabajo y gaming", price=1200.00, stock=10, category="Electrónica", image_url="/static/images/products/laptop.jpg"),
            Product(name="Mouse Inalámbrico", description="Mouse ergonómico con batería de 6 meses", price=35.50, stock=25, category="Electrónica", image_url="/static/images/products/mouse.jpg"),
            Product(name="Teclado Mecánico", description="Switch RGB retroiluminado, diseño compacto", price=89.99, stock=15, category="Electrónica", image_url="/static/images/products/teclado.jpg"),
            Product(name="Audífonos Bluetooth", description="Cancelación de ruido, 30h batería", price=59.99, stock=20, category="Electrónica", image_url="/static/images/products/audifonos.jpg"),
            Product(name='Monitor 27" 4K', description="Panel IPS, 144Hz, HDR10", price=450.00, stock=8, category="Electrónica", image_url="/static/images/products/monitor.jpg"),
            Product(name="Camiseta Algodón", description="100% algodón orgánico, varios colores", price=24.99, stock=50, category="Ropa", image_url="/static/images/products/camiseta.jpg"),
            Product(name="Chaqueta Impermeable", description="Capa ligera, resistente al agua", price=79.99, stock=12, category="Ropa", image_url="/static/images/products/chaqueta.jpg"),
            Product(name="Libro: Python Avanzado", description="Guía completa de Python 3.13", price=45.00, stock=30, category="Libros", image_url="/static/images/products/libro.jpg"),
        ]
        for p in products:
            session.add(p)
        session.commit()
        logger.info("  ✅ Created %d products across %d categories", len(products), len(set(p.category for p in products)))

        logger.info("🎉 Database seeded successfully!")
