"""Categories endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.categories import list_categories

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("")
async def list_categories_endpoint(
    session: AsyncSession = Depends(get_async_session),
) -> list[str]:
    """Return distinct categories from active products."""
    return await list_categories(session)