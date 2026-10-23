# NOTA: Alertas diários: contas a pagar que vencem em breve, recebíveis atrasados e prazos do Kanban.
#       Cada alerta é criado no máximo uma vez por empresa por dia.

"""Daily alerts (NOT-2): bills due soon, late receivables and Kanban deadlines. Each alert is created
at most once per company per day (the date is part of its title)."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.notify import notify_company
from app.db.models import FinancialEntryModel, KanbanCardModel, KanbanColumnModel, NotificationModel, ProjectModel
from app.integrations.ai.rules import brl

BILLS_AHEAD_DAYS = 3
TASKS_AHEAD_DAYS = 2
_DONE = ("concluido", "concluído", "done", "finalizado")


async def _already_sent(db: AsyncSession, company_id: str, title: str) -> bool:
    return (await db.execute(select(NotificationModel.id).where(
        NotificationModel.company_id == company_id, NotificationModel.title == title).limit(1))).scalar_one_or_none() is not None


async def _send(db: AsyncSession, company_id: str, title: str, message: str, kind: str) -> int:
    if await _already_sent(db, company_id, title):
        return 0
    await notify_company(db, company_id, title, message, kind=kind)
    return 1


def _summary(rows, limit=3) -> str:
    names = ", ".join(f"{(r.description or 'sem descrição')[:40]} ({brl(r.amount)})" for r in rows[:limit])
    return names + (f" e mais {len(rows) - limit}" if len(rows) > limit else "")


async def daily_alerts(db: AsyncSession, company_id: str) -> int:
    today = date.today()
    stamp = today.strftime("%d/%m")
    t, bills_until, tasks_until = today.isoformat(), (today + timedelta(days=BILLS_AHEAD_DAYS)).isoformat(), (today + timedelta(days=TASKS_AHEAD_DAYS)).isoformat()
    pending = list((await db.execute(select(FinancialEntryModel).where(
        FinancialEntryModel.company_id == company_id, FinancialEntryModel.status == "PENDENTE",
        FinancialEntryModel.due_date.is_not(None)))).scalars().all())
    sent = 0

    bills = sorted([e for e in pending if e.type == "DESPESA" and t <= e.due_date <= bills_until], key=lambda e: e.due_date)
    if bills:
        sent += await _send(db, company_id, f"Contas a pagar nos próximos {BILLS_AHEAD_DAYS} dias ({stamp})",
                            f"{len(bills)} conta(s), total de {brl(sum(e.amount for e in bills))}: {_summary(bills)}.", "WARNING")

    late = sorted([e for e in pending if e.type == "RECEITA" and e.due_date < t], key=lambda e: e.due_date)
    if late:
        sent += await _send(db, company_id, f"Recebimentos atrasados ({stamp})",
                            f"{len(late)} recebimento(s) vencido(s), total de {brl(sum(e.amount for e in late))}: {_summary(late)}.", "WARNING")

    cards = (await db.execute(
        select(KanbanCardModel.title, KanbanCardModel.due_date, KanbanColumnModel.name)
        .join(KanbanColumnModel, KanbanCardModel.column_id == KanbanColumnModel.id)
        .join(ProjectModel, KanbanColumnModel.project_id == ProjectModel.id)
        .where(ProjectModel.company_id == company_id, KanbanCardModel.due_date.is_not(None),
               KanbanCardModel.due_date <= tasks_until)
    )).all()
    open_cards = [c for c in cards if (c.name or "").strip().lower() not in _DONE]
    if open_cards:
        names = ", ".join(f"{c.title[:40]} ({c.due_date[8:10]}/{c.due_date[5:7]})" for c in open_cards[:3])
        sent += await _send(db, company_id, f"Tarefas com prazo próximo ({stamp})",
                            f"{len(open_cards)} tarefa(s) vencendo até {tasks_until[8:10]}/{tasks_until[5:7]} ou atrasadas: {names}.", "INFO")
    return sent
