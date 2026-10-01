"""Compact, real-data snapshots sent to the model (and used by the rule-based fallback).

Only aggregates and short descriptions of the caller's own company or person: no CPF,
e-mails or anything from other tenants.
"""

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models as m


def _r(v: float) -> float:
    return round(v or 0, 2)


async def business_snapshot(db: AsyncSession, company_id: str) -> dict:
    today = date.today()
    t, d30, d90, f30 = today.isoformat(), (today - timedelta(days=30)).isoformat(), (today - timedelta(days=90)).isoformat(), (today + timedelta(days=30)).isoformat()
    entries = (await db.execute(select(m.FinancialEntryModel).where(m.FinancialEntryModel.company_id == company_id))).scalars().all()

    def paid(kind: str, since: str) -> float:
        return sum(e.amount for e in entries if e.type == kind and e.status == "PAGO" and (e.payment_date or "") >= since)

    def items(rows):
        return [{"descricao": (e.description or "")[:60], "valor": _r(e.amount), "vencimento": e.due_date} for e in sorted(rows, key=lambda e: -e.amount)[:5]]

    pending = [e for e in entries if e.status == "PENDENTE" and e.due_date]
    payable = [e for e in pending if e.type == "DESPESA" and t <= e.due_date <= f30]
    receivable = [e for e in pending if e.type == "RECEITA" and t <= e.due_date <= f30]
    overdue = [e for e in pending if e.due_date < t]

    by_category: dict[str, float] = defaultdict(float)
    for e in entries:
        if e.type == "DESPESA" and e.status == "PAGO" and (e.payment_date or "") >= d90:
            by_category[e.category or "Sem categoria"] += e.amount
    total_exp_90 = sum(by_category.values())

    employees = (await db.execute(select(m.EmployeeModel).where(m.EmployeeModel.company_id == company_id, m.EmployeeModel.is_active == True))).scalars().all()  # noqa: E712
    projects = (await db.execute(select(func.count()).select_from(m.ProjectModel).where(m.ProjectModel.company_id == company_id))).scalar() or 0
    unreconciled = (await db.execute(select(func.count()).select_from(m.BankTransactionModel).where(
        m.BankTransactionModel.company_id == company_id, m.BankTransactionModel.owner_id.is_(None), m.BankTransactionModel.status == "NOVA"))).scalar() or 0

    return {
        "data_de_hoje": t,
        "ultimos_30_dias": {"receitas_recebidas": _r(paid("RECEITA", d30)), "despesas_pagas": _r(paid("DESPESA", d30))},
        "ultimos_90_dias": {"receitas_recebidas": _r(paid("RECEITA", d90)), "despesas_pagas": _r(paid("DESPESA", d90))},
        "proximos_30_dias": {
            "a_receber": _r(sum(e.amount for e in receivable)), "a_pagar": _r(sum(e.amount for e in payable)),
            "maiores_a_receber": items(receivable), "maiores_a_pagar": items(payable),
        },
        "vencidos": {"quantidade": len(overdue), "a_pagar": _r(sum(e.amount for e in overdue if e.type == "DESPESA")),
                     "a_receber": _r(sum(e.amount for e in overdue if e.type == "RECEITA"))},
        "despesas_por_categoria_90_dias": [
            {"categoria": k, "total": _r(v), "participacao": round(v / total_exp_90, 3) if total_exp_90 else 0}
            for k, v in sorted(by_category.items(), key=lambda kv: -kv[1])[:6]
        ],
        "equipe": {"colaboradores_ativos": len(employees), "custo_mensal_total": _r(sum(e.ctc_monthly or 0 for e in employees)),
                   "custo_hora_medio": _r(sum(e.hourly_cost or 0 for e in employees) / len(employees)) if employees else 0},
        "projetos": projects,
        "movimentacoes_bancarias_sem_conciliacao": unreconciled,
    }


async def personal_snapshot(db: AsyncSession, owner_id: str) -> dict:
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    three_months_ago = (today.replace(day=1) - timedelta(days=90)).replace(day=1).isoformat()

    async def owned(model):
        return (await db.execute(select(model).where(model.owner_id == owner_id))).scalars().all()

    accounts, debts, entries = await owned(m.PersonalAccountModel), await owned(m.PersonalDebtModel), await owned(m.PersonalEntryModel)
    budgets, subs, goals = await owned(m.PersonalBudgetModel), await owned(m.PersonalSubscriptionModel), await owned(m.PersonalGoalModel)

    spent_month: dict[str, float] = defaultdict(float)
    income_month = 0.0
    for e in entries:
        if (e.date or "") >= month_start:
            if e.type == "DESPESA":
                spent_month[e.category or "Outros"] += e.amount
            else:
                income_month += e.amount
    past_expenses = sum(e.amount for e in entries if e.type == "DESPESA" and three_months_ago <= (e.date or "") < month_start)
    active_subs = [s for s in subs if s.is_active]

    return {
        "data_de_hoje": today.isoformat(),
        "contas": [{"nome": a.name, "tipo": a.type, "saldo": _r(a.balance)} for a in accounts],
        "saldo_em_contas": _r(sum(a.balance or 0 for a in accounts if a.type != "CARTAO")),
        "fatura_cartoes": _r(-sum(a.balance or 0 for a in accounts if a.type == "CARTAO")),
        "dividas_restantes": _r(sum(d.remaining_amount or 0 for d in debts)),
        "mes_atual": {"receitas": _r(income_month), "gastos_por_categoria": {k: _r(v) for k, v in sorted(spent_month.items(), key=lambda kv: -kv[1])}},
        "despesa_media_mensal_3_meses": _r(past_expenses / 3),
        "orcamentos": [
            {"categoria": b.category, "limite": _r(b.limit_amount), "gasto_no_mes": _r(spent_month.get(b.category or "", 0)),
             "uso": round(spent_month.get(b.category or "", 0) / b.limit_amount, 3) if b.limit_amount else None}
            for b in budgets
        ],
        "assinaturas_ativas": {"quantidade": len(active_subs), "total_mensal": _r(sum(s.amount or 0 for s in active_subs)),
                               "nomes": [s.name for s in active_subs][:10]},
        "metas": [{"nome": g.name, "alvo": _r(g.target_amount), "atual": _r(g.current_amount), "prazo": g.target_date} for g in goals],
    }
