from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime, date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import FinancialEntryModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

hoje = date.today()
def dias(n): return (hoje + timedelta(days=n)).isoformat()

_FIN_COLUMNS = {c.name for c in FinancialEntryModel.__table__.columns}

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
):
    result = await db.execute(select(FinancialEntryModel))
    e = models_to_dicts(result.scalars().all())
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
async def create_entry(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    en_dict = {"id": f"fin-{uuid.uuid4().hex[:6]}", "status": "PENDENTE", "payment_date": None, **d}
    model_kwargs = {k: v for k, v in en_dict.items() if k in _FIN_COLUMNS}
    en = FinancialEntryModel(**model_kwargs)
    db.add(en)
    await db.commit()
    await db.refresh(en)
    return model_to_dict(en)


@router.get("/entries/{eid}")
async def get_entry(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(FinancialEntryModel, eid)
    if not e:
        raise HTTPException(404)
    return model_to_dict(e)


@router.put("/entries/{eid}")
async def upd_entry(eid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(FinancialEntryModel, eid)
    if not e:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _FIN_COLUMNS:
            setattr(e, k, v)
    await db.commit()
    await db.refresh(e)
    return model_to_dict(e)


@router.post("/entries/{eid}/pay")
async def pay_entry(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(FinancialEntryModel, eid)
    if not e:
        raise HTTPException(404)
    e.status = "PAGO"
    e.payment_date = date.today().isoformat()
    await db.commit()
    await db.refresh(e)
    return model_to_dict(e)


@router.post("/entries/{eid}/attachment")
async def attach(eid: str, u=Depends(get_current_user)):
    return {"attachment_url": f"/uploads/{eid}.pdf"}


@router.get("/dre")
async def get_dre(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    u=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FinancialEntryModel))
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
        "period": {"start": start_date or start or dias(-30), "end": end_date or end or dias(0)},
        "total_receitas": round(rec, 2),
        "total_despesas": round(desp, 2),
        "receitas": receitas_list,
        "despesas": despesas_list,
        "resultado_liquido": round(rec - desp, 2),
        "margem_percentual": margem,
    }


@router.get("/cashflow")
async def get_cashflow(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FinancialEntryModel))
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
    saldo_acumulado = saldo_atual
    for i in range(-30, 61):
        d = hoje_dt + timedelta(days=i)
        d_str = d.isoformat()
        rec_dia = sum(
            e.amount for e in entries
            if e.type == "RECEITA"
            and ((e.payment_date == d_str) if e.status == "PAGO" else (e.due_date == d_str))
        )
        desp_dia = sum(
            e.amount for e in entries
            if e.type == "DESPESA"
            and ((e.payment_date == d_str) if e.status == "PAGO" else (e.due_date == d_str))
        )
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
async def get_monthly_summary(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retorna receitas e despesas agrupadas por mês (últimos 6 meses), para o gráfico do Dashboard."""
    result = await db.execute(select(FinancialEntryModel))
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
