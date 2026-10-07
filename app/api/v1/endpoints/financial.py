import os
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response
import mimetypes
from typing import Optional
import uuid
from datetime import datetime, date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core import audit, storage
from app.core.permissions import require_module
from app.db.session import get_db
from app.db.models import FinancialEntryModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

hoje = date.today()
def dias(n): return (hoje + timedelta(days=n)).isoformat()

_FIN_COLUMNS = {c.name for c in FinancialEntryModel.__table__.columns}
# Set by the server only; never accepted from a request body.
_FIN_PROTECTED = {"id", "company_id", "attachment_name", "attachment_key"}


def _entry_out(e) -> dict:
    d = model_to_dict(e)
    d.pop("attachment_key", None)
    return d


async def _check_supplier(db: AsyncSession, supplier_id, company_id: str) -> None:
    if supplier_id:
        from app.db.models import SupplierModel
        supplier = await db.get(SupplierModel, supplier_id)
        if not supplier or supplier.company_id != company_id:
            raise HTTPException(404, "Fornecedor não encontrado")

MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


@router.get("/entries")
async def get_entries(
    skip: int = 0,
    size: int = 50,
    page: int = 1,
    type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None,
    u=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _p=Depends(require_module("financeiro")),
):
    result = await db.execute(select(FinancialEntryModel).where(FinancialEntryModel.company_id == u["company_id"]))
    e = [_entry_out(x) for x in result.scalars().all()]
    if type:
        e = [x for x in e if x["type"] == type]
    if status:
        e = [x for x in e if x["status"] == status]
    if category:
        e = [x for x in e if (x.get("category") or "").lower() == category.lower()]
    if search:
        s = search.lower()
        e = [x for x in e if s in (x.get("description") or "").lower()
             or s in (x.get("category") or "").lower()
             or s in (x.get("cost_center") or "").lower()]
    if page > 1:
        skip = (page - 1) * size
    total = len(e)
    return {"items": e[skip:skip + size], "total": total, "page": page, "size": size, "pages": (total + size - 1) // size}


@router.post("/entries")
async def create_entry(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    try:
        amount = float(d.get("amount", 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "Valor do lançamento inválido")
    if d.get("type") not in {"RECEITA", "DESPESA"} or amount <= 0:
        raise HTTPException(400, "Tipo ou valor do lançamento inválido")
    d = {k: v for k, v in d.items() if k not in _FIN_PROTECTED}
    d["amount"] = amount
    await _check_supplier(db, d.get("supplier_id"), u["company_id"])
    en_dict = {**d, "id": f"fin-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"], "status": "PENDENTE", "payment_date": None}
    model_kwargs = {k: v for k, v in en_dict.items() if k in _FIN_COLUMNS}
    en = FinancialEntryModel(**model_kwargs)
    db.add(en)
    audit.record_by(db, u, "LANCAMENTO_CRIADO", entity="financial_entry", entity_id=en.id, details={"tipo": en.type, "valor": en.amount, "descricao": en.description})
    await db.commit()
    await db.refresh(en)
    return _entry_out(en)


@router.get("/entries/{eid}")
async def get_entry(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    e = await db.get(FinancialEntryModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    return _entry_out(e)


@router.put("/entries/{eid}")
async def upd_entry(eid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    e = await db.get(FinancialEntryModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    changes = {k: v for k, v in d.items() if k in _FIN_COLUMNS and k not in _FIN_PROTECTED}
    if "supplier_id" in changes:
        await _check_supplier(db, changes["supplier_id"], u["company_id"])
    for k, v in changes.items():
        setattr(e, k, v)
    audit.record_by(db, u, "LANCAMENTO_ALTERADO", entity="financial_entry", entity_id=eid, details=changes)
    await db.commit()
    await db.refresh(e)
    return _entry_out(e)


@router.post("/entries/{eid}/pay")
async def pay_entry(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    e = await db.get(FinancialEntryModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    e.status = "PAGO"
    e.payment_date = date.today().isoformat()
    audit.record_by(db, u, "LANCAMENTO_PAGO", entity="financial_entry", entity_id=eid, details={"valor": e.amount})
    await db.commit()
    await db.refresh(e)
    return _entry_out(e)


@router.post("/entries/{eid}/attachment")
async def attach(eid: str, file: UploadFile = File(...), u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    entry = await db.get(FinancialEntryModel, eid)
    if not entry or entry.company_id != u["company_id"]:
        raise HTTPException(404)
    filename = os.path.basename(file.filename or "anexo")
    if not storage.extension_allowed(filename):
        raise HTTPException(400, "Tipo de arquivo não permitido. Use PDF, imagem (PNG/JPG/WEBP) ou XML de nota fiscal")
    content = await file.read(storage.MAX_ATTACHMENT_BYTES + 1)
    if len(content) > storage.MAX_ATTACHMENT_BYTES:
        raise HTTPException(413, "Arquivo maior que 10 MB")
    old_key = entry.attachment_key
    entry.attachment_key = await storage.save_attachment(u["company_id"], filename, content)
    entry.attachment_name = filename
    audit.record_by(db, u, "ANEXO_ENVIADO", entity="financial_entry", entity_id=eid, details={"arquivo": filename, "bytes": len(content)})
    await db.commit()
    if old_key:
        await storage.delete_attachment(old_key)
    await db.refresh(entry)
    return _entry_out(entry)


@router.get("/entries/{eid}/attachment")
async def download_attachment(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    entry = await db.get(FinancialEntryModel, eid)
    if not entry or entry.company_id != u["company_id"] or not entry.attachment_key:
        raise HTTPException(404, "Anexo não encontrado")
    content = await storage.read_attachment(entry.attachment_key)
    if content is None:
        raise HTTPException(404, "Anexo não encontrado")
    name = (entry.attachment_name or "comprovante").replace('"', "")
    media = mimetypes.guess_type(name)[0] or "application/octet-stream"
    return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/dre")
async def get_dre(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    u=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _p=Depends(require_module("financeiro")),
):
    period_start = start_date or start or dias(-30)
    period_end = end_date or end or dias(0)
    if period_start > period_end:
        raise HTTPException(400, "Período inválido")
    result = await db.execute(
        select(FinancialEntryModel).where(
            FinancialEntryModel.company_id == u["company_id"],
            FinancialEntryModel.due_date >= period_start,
            FinancialEntryModel.due_date <= period_end,
        )
    )
    entries = result.scalars().all()

    rec = sum(e.amount for e in entries if e.type == "RECEITA")
    desp = sum(e.amount for e in entries if e.type == "DESPESA")

    # Agrega receitas por categoria real do banco
    receitas_map: dict = {}
    for e in entries:
        if e.type == "RECEITA":
            cat = e.category or "Sem categoria"
            receitas_map[cat] = receitas_map.get(cat, 0.0) + e.amount

    # Agrega despesas por categoria real do banco
    despesas_map: dict = {}
    for e in entries:
        if e.type == "DESPESA":
            cat = e.category or "Sem categoria"
            despesas_map[cat] = despesas_map.get(cat, 0.0) + e.amount

    receitas_list = [{"categoria": k, "total": round(v, 2)} for k, v in sorted(receitas_map.items(), key=lambda x: -x[1])]
    despesas_list = [{"categoria": k, "total": round(v, 2)} for k, v in sorted(despesas_map.items(), key=lambda x: -x[1])]

    margem = round((rec - desp) / rec * 100, 1) if rec else 0.0

    return {
        "period": {"start": period_start, "end": period_end},
        "total_receitas": round(rec, 2),
        "total_despesas": round(desp, 2),
        "receitas": receitas_list,
        "despesas": despesas_list,
        "resultado_liquido": round(rec - desp, 2),
        "margem_percentual": margem,
    }


@router.get("/cashflow")
async def get_cashflow(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    result = await db.execute(select(FinancialEntryModel).where(FinancialEntryModel.company_id == u["company_id"]))
    entries = result.scalars().all()

    # Saldo atual = lançamentos PAGOS (receitas - despesas)
    saldo_atual = round(
        sum(e.amount if e.type == "RECEITA" else -e.amount for e in entries if e.status == "PAGO"),
        2,
    )

    # Projeção 30 dias: lançamentos PENDENTES com due_date no período
    hoje_dt = date.today()
    limite_30d = hoje_dt + timedelta(days=30)
    hoje_str = hoje_dt.isoformat()
    limite_str = limite_30d.isoformat()

    receitas_previstas = round(
        sum(
            e.amount for e in entries
            if e.type == "RECEITA" and e.status == "PENDENTE"
            and e.due_date and hoje_str <= e.due_date <= limite_str
        ),
        2,
    )
    despesas_previstas = round(
        sum(
            e.amount for e in entries
            if e.type == "DESPESA" and e.status == "PENDENTE"
            and e.due_date and hoje_str <= e.due_date <= limite_str
        ),
        2,
    )

    projected_balance = round(saldo_atual + receitas_previstas - despesas_previstas, 2)

    # Nível de alerta
    if saldo_atual == 0:
        alert_level = "VERDE" if projected_balance >= 0 else "VERMELHO"
    elif projected_balance >= saldo_atual * 0.8:
        alert_level = "VERDE"
    elif projected_balance >= 0:
        alert_level = "AMARELO"
    else:
        alert_level = "VERMELHO"

    # Série temporal D-30 até D+60 com lançamentos reais por data
    items = []
    series_start = hoje_dt - timedelta(days=30)
    saldo_acumulado = round(
        sum(
            e.amount if e.type == "RECEITA" else -e.amount
            for e in entries
            if e.status == "PAGO" and e.payment_date and e.payment_date < series_start.isoformat()
        ),
        2,
    )
    for i in range(-30, 61):
        d = hoje_dt + timedelta(days=i)
        d_str = d.isoformat()
        rec_dia = sum(e.amount for e in entries if e.type == "RECEITA" and (
            (e.status == "PAGO" and e.payment_date == d_str)
            or (d > hoje_dt and e.status == "PENDENTE" and e.due_date == d_str)
        ))
        desp_dia = sum(e.amount for e in entries if e.type == "DESPESA" and (
            (e.status == "PAGO" and e.payment_date == d_str)
            or (d > hoje_dt and e.status == "PENDENTE" and e.due_date == d_str)
        ))
        saldo_acumulado = round(saldo_acumulado + rec_dia - desp_dia, 2)
        items.append({
            "date": d_str,
            "receitas": round(rec_dia, 2),
            "despesas": round(desp_dia, 2),
            "saldo_acumulado": saldo_acumulado,
        })

    return {
        "items": items,
        "saldo_atual": saldo_atual,
        "current_balance": saldo_atual,
        "receitas_previstas_30d": receitas_previstas,
        "projected_income": receitas_previstas,
        "despesas_previstas_30d": despesas_previstas,
        "projected_expense": despesas_previstas,
        "projected_balance": projected_balance,
        "alert_level": alert_level,
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/monthly-summary")
async def get_monthly_summary(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("financeiro"))):
    """Retorna receitas e despesas agrupadas por mês (últimos 6 meses), para o gráfico do Dashboard."""
    result = await db.execute(select(FinancialEntryModel).where(FinancialEntryModel.company_id == u["company_id"]))
    entries = result.scalars().all()

    hoje_dt = date.today()
    meses = []
    for i in range(5, -1, -1):
        # Calcula o mês corretamente retrocedendo i meses
        total_months = hoje_dt.month - 1 - i
        year = hoje_dt.year + total_months // 12
        month = total_months % 12 + 1
        meses.append((year, month))

    summary = []
    for year, month in meses:
        label = MONTH_LABELS[month - 1]
        prefix = f"{year:04d}-{month:02d}-"
        rec = round(sum(e.amount for e in entries if e.type == "RECEITA" and e.due_date and e.due_date.startswith(prefix)), 2)
        desp = round(sum(e.amount for e in entries if e.type == "DESPESA" and e.due_date and e.due_date.startswith(prefix)), 2)
        summary.append({"name": label, "year": year, "month": month, "receitas": rec, "despesas": desp})

    return {"items": summary}


@router.get("/dashboard/entries")
async def dashboard_entries(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("dashboard"))):
    result = await db.execute(
        select(FinancialEntryModel)
        .where(FinancialEntryModel.company_id == u["company_id"])
        .order_by(FinancialEntryModel.due_date.desc())
        .limit(5)
    )
    items = models_to_dicts(result.scalars().all())
    return {"items": items, "total": len(items), "page": 1, "size": 5, "pages": 1}


@router.get("/dashboard/dre")
async def dashboard_dre(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("dashboard"))):
    return await get_dre(u=u, db=db, _p=u)


@router.get("/dashboard/cashflow")
async def dashboard_cashflow(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("dashboard"))):
    return await get_cashflow(u=u, db=db, _p=u)


@router.get("/dashboard/monthly-summary")
async def dashboard_monthly_summary(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("dashboard"))):
    return await get_monthly_summary(u=u, db=db, _p=u)
