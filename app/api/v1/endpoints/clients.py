# NOTA: Rotas /clients: cadastro de clientes da empresa (listar, criar, editar, excluir).

from fastapi import APIRouter, HTTPException, Depends
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import ClientModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_CLIENT_COLUMNS = {c.name for c in ClientModel.__table__.columns}

@router.get("/")
async def get_clients(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClientModel).where(ClientModel.company_id == u["company_id"]))
    return models_to_dicts(result.scalars().all())

@router.post("/")
async def create_client(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c_dict = {**d, "id": f"cli-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"]}
    model_kwargs = {k: v for k, v in c_dict.items() if k in _CLIENT_COLUMNS}
    c = ClientModel(**model_kwargs)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return model_to_dict(c)

@router.put("/{cid}")
async def upd_client(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await db.get(ClientModel, cid)
    if not c or c.company_id != u["company_id"]:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _CLIENT_COLUMNS and k not in {"id", "company_id"}:
            setattr(c, k, v)
    await db.commit()
    await db.refresh(c)
    return model_to_dict(c)

@router.delete("/{cid}")
async def del_client(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    c = await db.get(ClientModel, cid)
    if not c or c.company_id != u["company_id"]:
        raise HTTPException(404)
    await db.delete(c)
    await db.commit()
    return {"success": True}
