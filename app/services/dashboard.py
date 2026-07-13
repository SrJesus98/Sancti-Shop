from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, Product, User

async def get_dashboard_metrics(session: AsyncSession) -> dict:

    result = await session.execute(select(func.count()).select_from(User)) ## Obtiene la cantidad de Usuarios
    cant_usuarios = result.scalar() or 0
    
    result = await session.execute(select(func.count()).select_from(Product).where(Product.is_active==True)) ## Obtiene la cantidad de Productos
    cant_productos = result.scalar() or 0

    result = await session.execute(select(func.count()).select_from(Order)) ## Obtiene la cantidad de Ordenes
    cant_ordenes = result.scalar() or 0

    result = await session.execute(select(Order.status, func.count()).group_by(Order.status))## Obtiene la cantidad de Ordenes por estado
    cant_oredenes_x_estado = dict(result.all())
    
    result = await session.execute(select(Order.total).where(Order.status.in_(["Pagada", "Entregada"]))) ## Obtiene los Ingresos Totales
    ingresos_totales = sum(result.scalars().all())

    return {
        "total_usuarios": cant_usuarios,  
        "total_productos": cant_productos,
        "total_ordenes": cant_ordenes,
        "oredenes_x_estado": cant_oredenes_x_estado,
        "ingresos_totales": ingresos_totales
    }

