# NOTA: Rotas /suppliers: cadastro de fornecedores (listar, criar, ver, editar, excluir).

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import SupplierModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_SUP_COLUMNS = {c.name for c in SupplierModel.__table__.columns}


@router.get("/")
async def get_sups(active_only: Optional[bool] = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(SupplierModel).where(SupplierModel.company_id == u["company_id"])
    if active_only is not None:
        stmt = stmt.where(SupplierModel.is_active == active_only)
    result = await db.execute(stmt)
    return models_to_dicts(result.scalars().all())


@router.post("/")
async def create_sup(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sup_dict = {**d, "id": f"sup-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"], "is_active": True}
    model_kwargs = {k: v for k, v in sup_dict.items() if k in _SUP_COLUMNS}
    s = SupplierModel(**model_kwargs)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return model_to_dict(s)


@router.delete("/{sid}")
async def del_sup(sid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    s = await db.get(SupplierModel, sid)
    if not s or s.company_id != u["company_id"]:
        raise HTTPException(404)
    await db.delete(s)
    await db.commit()
    return {"success": True}


@router.get("/{sid}")
async def get_sup(sid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    s = await db.get(SupplierModel, sid)
    if not s or s.company_id != u["company_id"]:
        raise HTTPException(404)
    return model_to_dict(s)


@router.put("/{sid}")
async def upd_sup(sid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    s = await db.get(SupplierModel, sid)
    if not s or s.company_id != u["company_id"]:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _SUP_COLUMNS and k not in {"id", "company_id"}:
            setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return model_to_dict(s)
