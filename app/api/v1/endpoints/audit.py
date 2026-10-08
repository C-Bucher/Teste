from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.models import AuditLogModel
from app.db.session import get_db
from app.db.utils import models_to_dicts

router = APIRouter()


@router.get("/")
async def list_audit(
    page: int = 1,
    size: int = 50,
    action: Optional[str] = None,
    u=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem consultar a auditoria")
    page, size = max(page, 1), min(max(size, 1), 200)
    where = [AuditLogModel.company_id == u["company_id"]]
    if action:
        where.append(AuditLogModel.action == action)
    total = (await db.execute(select(func.count()).select_from(AuditLogModel).where(*where))).scalar() or 0
    rows = (await db.execute(
        select(AuditLogModel).where(*where).order_by(AuditLogModel.created_at.desc()).offset((page - 1) * size).limit(size)
    )).scalars().all()
    return {"items": models_to_dicts(rows), "total": total, "page": page, "size": size}
