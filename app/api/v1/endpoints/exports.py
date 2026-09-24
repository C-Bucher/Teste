from fastapi import APIRouter, HTTPException, Depends, Request
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import ExportLogModel, FinancialEntryModel, EmployeeModel, SupplierModel, ProjectModel, KanbanColumnModel, KanbanCardModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_EXPORT_COLUMNS = {c.name for c in ExportLogModel.__table__.columns}

import os
import json

@router.get("/")
async def get_exports_main(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel).where(ExportLogModel.company_id == u["company_id"]).order_by(ExportLogModel.created_at.desc()))
    return models_to_dicts(result.scalars().all())

@router.post("/request")
async def req_export(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    eid = f"exp-{uuid.uuid4().hex}"
    exp_type = d.get("type", "RELATORIO")
    exp_format = d.get("format", "CSV").upper()
    if exp_format not in {"CSV", "JSON"}:
        raise HTTPException(400, "Formato não suportado. Use CSV ou JSON")
    
    # Generate mock exported file
    os.makedirs("uploads", exist_ok=True)
    filename = f"export_{eid}.{exp_format.lower()}"
    filepath = os.path.join("uploads", filename)
    
    if exp_type in {"DRE", "FLUXO_CAIXA"}:
        result = await db.execute(select(FinancialEntryModel).where(FinancialEntryModel.company_id == u["company_id"]))
        rows = models_to_dicts(result.scalars().all())
    elif exp_type == "COLABORADORES":
        result = await db.execute(select(EmployeeModel).where(EmployeeModel.company_id == u["company_id"]))
        rows = models_to_dicts(result.scalars().all())
    elif exp_type == "FORNECEDORES":
        result = await db.execute(select(SupplierModel).where(SupplierModel.company_id == u["company_id"]))
        rows = models_to_dicts(result.scalars().all())
    elif exp_type == "COST_PER_TASK":
        result = await db.execute(
            select(KanbanCardModel)
            .join(KanbanColumnModel, KanbanCardModel.column_id == KanbanColumnModel.id)
            .join(ProjectModel, KanbanColumnModel.project_id == ProjectModel.id)
            .where(ProjectModel.company_id == u["company_id"])
        )
        rows = models_to_dicts(result.scalars().all())
    else:
        raise HTTPException(400, "Tipo de relatório não suportado")
    if exp_format == "JSON":
        content = json.dumps({"tipo": exp_type, "gerado_em": datetime.now().isoformat(), "items": rows}, ensure_ascii=False, indent=2)
    else:
        headers = list(rows[0].keys()) if rows else []
        def csv_value(value):
            return '"' + str(value if value is not None else "").replace('"', '""') + '"'
        content = ",".join(headers) + "\n"
        content += "\n".join(",".join(csv_value(row.get(header)) for header in headers) for row in rows)
        if rows:
            content += "\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    size_bytes = os.path.getsize(filepath)
    
    ex_dict = {
        "id": eid,
        "company_id": u["company_id"],
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
    result = await db.execute(select(ExportLogModel).where(ExportLogModel.company_id == u["company_id"]).order_by(ExportLogModel.created_at.desc()))
    return models_to_dicts(result.scalars().all())

@router.get("/download/{eid}")
async def dl_export(eid: str, request: Request, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    base_url = str(request.base_url).rstrip("/")
    export = await db.get(ExportLogModel, eid)
    if not export or export.company_id != u["company_id"]:
        raise HTTPException(404, "Exportação não encontrada")

    # Check if file exists in uploads
    for ext in ["csv", "json"]:
        candidate = f"export_{eid}.{ext}"
        if os.path.exists(os.path.join("uploads", candidate)):
            return {"download_url": f"{base_url}/uploads/{candidate}", "filename": candidate}

    raise HTTPException(404, "Arquivo de exportação não encontrado")
