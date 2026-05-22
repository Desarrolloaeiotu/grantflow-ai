import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.models.funder import Funder
from app.schemas.funder import FunderList, FunderRead

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=FunderList)
async def list_funders(
    name: str | None = Query(None, description="Buscar por nombre (ILIKE)"),
    has_history: bool | None = Query(None, description="Solo financiadores con historial aeioTU"),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(require_api_key),
) -> FunderList:
    """Lista todos los financiadores con filtros opcionales."""
    query = select(Funder)

    if name:
        query = query.where(Funder.name.ilike(f"%{name}%"))
    if has_history is not None:
        query = query.where(Funder.has_history == has_history)

    # Contar total
    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar_one()

    # Paginar
    query = query.order_by(Funder.name).offset((page - 1) * size).limit(size)
    rows = (await db.execute(query)).scalars().all()

    return FunderList(items=list(rows), total=total, page=page, size=size)


@router.get("/{funder_id}", response_model=FunderRead)
async def get_funder(
    funder_id: str, db: AsyncSession = Depends(get_db), _auth: None = Depends(require_api_key)
) -> FunderRead:
    """Obtiene los detalles de un financiador específico."""
    from uuid import UUID

    result = await db.execute(select(Funder).where(Funder.id == UUID(funder_id)))
    funder = result.scalar_one_or_none()

    if not funder:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Funder not found")

    return FunderRead.model_validate(funder)
