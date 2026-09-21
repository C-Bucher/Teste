from fastapi import APIRouter, HTTPException, Depends, Request
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

import os
import io
import csv

@router.get("/")
async def get_exports_main(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel).order_by(ExportLogModel.created_at.desc()))
    return models_to_dicts(result.scalars().all())

@router.post("/request")
async def req_export(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    eid = f"exp-{uuid.uuid4().hex[:6]}"
    exp_type = d.get("type", "RELATORIO")
    exp_format = d.get("format", "CSV").upper()
    
    # Generate mock exported file
    os.makedirs("uploads", exist_ok=True)
    filename = f"export_{eid}.{exp_format.lower() if exp_format in ['csv', 'pdf', 'xlsx', 'json'] else 'csv'}"
    filepath = os.path.join("uploads", filename)
    
    content = f"TechConnect 2.0 - Relatorio {exp_type}\nData de Geracao: {datetime.now().strftime('%d/%m/%Y %H:%M')}\nTipo: {exp_type}\nFormato: {exp_format}\nStatus: Concluido\n\nID,Descricao,Valor,Status\n1,Lancamento Exemplo 1,1500.00,PAGO\n2,Lancamento Exemplo 2,2850.50,PAGO\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    size_bytes = os.path.getsize(filepath)
    
    ex_dict = {
        "id": eid,
        "type": exp_type,
        "format": exp_format,
        "status": "PRONTO",
        "created_at": datetime.now().isoformat(),
        "size_bytes": size_bytes
    }
    model_kwargs = {k: v for k, v in ex_dict.items() if k in _EXPORT_COLUMNS}
    ex = ExportLogModel(**model_kwargs)
    db.add(ex)
    await db.commit()
    await db.refresh(ex)
    return model_to_dict(ex)

@router.get("/logs")
async def get_exports(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel).order_by(ExportLogModel.created_at.desc()))
    return models_to_dicts(result.scalars().all())

@router.get("/download/{eid}")
async def dl_export(eid: str, request: Request, u=Depends(get_current_user)):
    base_url = str(request.base_url).rstrip("/")

    # Check if file exists in uploads
    for ext in ["csv", "pdf", "xlsx", "json"]:
        candidate = f"export_{eid}.{ext}"
        if os.path.exists(os.path.join("uploads", candidate)):
            return {"download_url": f"{base_url}/uploads/{candidate}", "filename": candidate, "expires_in": 3600}

    # Fallback created on the fly
    filename = f"export_{eid}.csv"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TechConnect 2.0 - Exportacao {eid}\nData: {datetime.now().isoformat()}\n")
    return {"download_url": f"{base_url}/uploads/{filename}", "filename": filename, "expires_in": 3600}
