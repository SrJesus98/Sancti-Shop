"""Categories service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product


async def list_categories(session: AsyncSession) -> list[str]:
    """Return distinct categories from active products."""
    result = await session.execute(
        select(Product.category)
        .where(Product.is_active == True)
        .where(Product.category.isnot(None))
        .distinct()
    )
    categories = result.scalars().all()
    return categories