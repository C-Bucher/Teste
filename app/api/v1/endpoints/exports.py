# NOTA: Rotas /exports: gera relatórios em CSV, JSON, XLSX ou PDF com os dados reais, lista o histórico e baixa o arquivo.

"""Reports built from the company's real data, in CSV, JSON, XLSX or PDF (EXP-1).
Files go to private storage and are downloaded only by the owning company."""

import io
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.core.security import get_current_user
from app.db.models import (EmployeeModel, ExportLogModel, FinancialEntryModel, KanbanCardModel, KanbanColumnModel,
                           ProjectModel, SupplierModel)
from app.db.session import get_db
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_EXPORT_COLUMNS = {c.name for c in ExportLogModel.__table__.columns}
FORMATS = {
    "CSV": ("csv", "text/csv"),
    "JSON": ("json", "application/json"),
    "XLSX": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "PDF": ("pdf", "application/pdf"),
}
TITLES = {"DRE": "Lançamentos (DRE)", "FLUXO_CAIXA": "Lançamentos (fluxo de caixa)", "COLABORADORES": "Colaboradores",
          "FORNECEDORES": "Fornecedores", "COST_PER_TASK": "Cost-per-Task"}
# Columns that only matter to the system, never to the person reading the report.
_HIDDEN = {"company_id", "attachment_key", "owner_id"}


async def _rows(db: AsyncSession, exp_type: str, company_id: str) -> list[dict]:
    if exp_type in {"DRE", "FLUXO_CAIXA"}:
        q = select(FinancialEntryModel).where(FinancialEntryModel.company_id == company_id)
    elif exp_type == "COLABORADORES":
        q = select(EmployeeModel).where(EmployeeModel.company_id == company_id)
    elif exp_type == "FORNECEDORES":
        q = select(SupplierModel).where(SupplierModel.company_id == company_id)
    elif exp_type == "COST_PER_TASK":
        q = (select(KanbanCardModel).join(KanbanColumnModel, KanbanCardModel.column_id == KanbanColumnModel.id)
             .join(ProjectModel, KanbanColumnModel.project_id == ProjectModel.id).where(ProjectModel.company_id == company_id))
    else:
        raise HTTPException(400, "Tipo de relatório não suportado")
    return [{k: v for k, v in r.items() if k not in _HIDDEN} for r in models_to_dicts((await db.execute(q)).scalars().all())]


def _is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def _safe_cell(value) -> str:
    """Spreadsheet formula injection: a text cell starting with = + - @ is prefixed with a quote."""
    text = str(value if value is not None else "")
    return "'" + text if text[:1] in ("=", "+", "-", "@") and not _is_number(text) else text


def _csv(rows: list[dict]) -> bytes:
    headers = list(rows[0].keys()) if rows else []
    lines = [",".join(headers)] + [",".join('"' + _safe_cell(r.get(h)).replace('"', '""') + '"' for h in headers) for r in rows]
    return ("\n".join(lines) + ("\n" if rows else "")).encode("utf-8")


def _xlsx(rows: list[dict], title: str) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    headers = list(rows[0].keys()) if rows else []
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for r in rows:
        ws.append([v if isinstance(v, (int, float)) or v is None else _safe_cell(v) for v in (r.get(h) for h in headers)])
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = min(40, max(10, *(len(str(c.value or "")) + 2 for c in column)))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _pdf(rows: list[dict], title: str, company: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    cell = styles["BodyText"].clone("cell", fontSize=7, leading=8)
    headers = list(rows[0].keys()) if rows else []
    data = [[Paragraph(f"<b>{h}</b>", cell) for h in headers]] + [[Paragraph(str(r.get(h) if r.get(h) is not None else ""), cell) for h in headers] for r in rows]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24, title=title)
    story = [Paragraph(f"{title} — {company}", styles["Title"]),
             Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · {len(rows)} registro(s)", styles["Normal"]), Spacer(1, 12)]
    if rows:
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF9")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(table)
    else:
        story.append(Paragraph("Nenhum registro.", styles["Normal"]))
    doc.build(story)
    return buf.getvalue()


@router.get("/")
async def get_exports_main(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel).where(ExportLogModel.company_id == u["company_id"]).order_by(ExportLogModel.created_at.desc()))
    return models_to_dicts(result.scalars().all())


@router.post("/request")
async def req_export(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    exp_type = str(d.get("type", "")).upper()
    exp_format = str(d.get("format", "CSV")).upper()
    if exp_format not in FORMATS:
        raise HTTPException(400, "Formato não suportado. Use CSV, JSON, XLSX ou PDF")
    rows = await _rows(db, exp_type, u["company_id"])
    title = TITLES.get(exp_type, exp_type)
    if exp_format == "JSON":
        content = json.dumps({"tipo": exp_type, "gerado_em": datetime.now().isoformat(), "items": rows}, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    elif exp_format == "XLSX":
        content = _xlsx(rows, title)
    elif exp_format == "PDF":
        from app.db.models import CompanyModel
        company = await db.get(CompanyModel, u["company_id"])
        content = _pdf(rows, title, company.name if company else "")
    else:
        content = _csv(rows)

    eid = f"exp-{uuid.uuid4().hex}"
    ext, mime = FORMATS[exp_format]
    await storage.save_export(u["company_id"], f"export_{eid}.{ext}", content, mime)
    ex = ExportLogModel(**{k: v for k, v in {
        "id": eid, "company_id": u["company_id"], "type": exp_type, "format": exp_format, "status": "PRONTO",
        "created_at": datetime.now().isoformat(), "size_bytes": len(content),
    }.items() if k in _EXPORT_COLUMNS})
    db.add(ex)
    await db.commit()
    await db.refresh(ex)
    return model_to_dict(ex)


@router.get("/logs")
async def get_exports(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportLogModel).where(ExportLogModel.company_id == u["company_id"]).order_by(ExportLogModel.created_at.desc()))
    return models_to_dicts(result.scalars().all())


@router.get("/download/{eid}")
async def dl_export(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    export = await db.get(ExportLogModel, eid)
    if not export or export.company_id != u["company_id"]:
        raise HTTPException(404, "Exportação não encontrada")
    ext, mime = FORMATS.get((export.format or "CSV").upper(), FORMATS["CSV"])
    content = await storage.read_export(export.company_id, f"export_{eid}.{ext}")
    if content is None:
        raise HTTPException(404, "Arquivo de exportação não encontrado")
    filename = f"{(export.type or 'relatorio').lower()}_{eid[-8:]}.{ext}"
    return Response(content, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
