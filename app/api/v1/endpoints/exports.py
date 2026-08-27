from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import ExportLogModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_EXPORT_COLUMNS = {c.name for c in ExportLogModel.__table__.columns}

@router.get("/")
async def get_exports_main(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel))
    return models_to_dicts(result.scalars().all())

@router.post("/request")
async def req_export(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ex_dict = {"id": f"exp-{uuid.uuid4().hex[:6]}", "status": "PROCESSANDO", "created_at": datetime.now().isoformat(), **d}
    model_kwargs = {k: v for k, v in ex_dict.items() if k in _EXPORT_COLUMNS}
    ex = ExportLogModel(**model_kwargs)
    db.add(ex)
    await db.commit()
    await db.refresh(ex)
    return model_to_dict(ex)

@router.get("/logs")
async def get_exports(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel))
    return models_to_dicts(result.scalars().all())

@router.get("/download/{eid}")
async def dl_export(eid: str, u=Depends(get_current_user)): return {"download_url":f"/uploads/export_{eid}.pdf","expires_in":3600}
