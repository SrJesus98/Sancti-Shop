#Importaciones
from fastapi import APIRouter, Depends #Router y Depends para usar las dependencias
from sqlalchemy.ext.asyncio import AsyncSession #Importa la session asincrona

from app.api.dependencies.auth import require_scopes
from app.db.session import get_async_session
#from app.db.models import User
from app.services.dashboard import get_dashboard_metrics

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/metrics", dependencies=[Depends(require_scopes(["admin:users"]))])
async def get_metrics(
    session:AsyncSession = Depends(get_async_session),
) -> dict:
    return await get_dashboard_metrics(session)
    
