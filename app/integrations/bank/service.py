# NOTA: Grava as transações do extrato sem duplicar e concilia cada uma com contas a pagar/receber (mesmo valor, até 5 dias de diferença).

"""Storing bank transactions and reconciling them with the company's payables/receivables."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.money import money, decimal_value
from app.db.models import (BankAccountModel, BankTransactionModel, CategorizationRuleModel,
                           FinancialEntryModel, PersonalEntryModel)
from app.integrations.bank.statement import ParsedTransaction

MATCH_WINDOW_DAYS = 5
AMOUNT_TOLERANCE = decimal_value("0.01")


def _days_between(a: str, b: str) -> int:
    return abs((date.fromisoformat(a[:10]) - date.fromisoformat(b[:10])).days)


def amounts_match(tx_amount: float, entry: FinancialEntryModel) -> bool:
    expected_type = "RECEITA" if tx_amount > 0 else "DESPESA"
    return entry.type == expected_type and abs(abs(money(tx_amount)) - money(entry.amount or 0)) <= AMOUNT_TOLERANCE


async def _rules(db: AsyncSession, account: BankAccountModel) -> list[CategorizationRuleModel]:
    q = select(CategorizationRuleModel).where(
        CategorizationRuleModel.company_id == account.company_id if account.company_id else CategorizationRuleModel.owner_id == account.owner_id
    )
    return list((await db.execute(q)).scalars().all())


async def ingest(db: AsyncSession, account: BankAccountModel, parsed: list[ParsedTransaction], u: dict) -> dict:
    """Saves new transactions (duplicates skipped), categorizes them, then reconciles (empresa)
    or turns them into personal entries (pessoal). Caller commits."""
    existing = set((await db.execute(
        select(BankTransactionModel.external_id).where(BankTransactionModel.bank_account_id == account.id)
    )).scalars().all())
    rules = await _rules(db, account)

    new: list[BankTransactionModel] = []
    duplicates = 0
    for p in parsed:
        if p.external_id in existing:
            duplicates += 1
            continue
        existing.add(p.external_id)
        desc = (p.description or "").lower()
        category = next((r.category for r in rules if r.pattern.lower() in desc), None)
        tx = BankTransactionModel(
            id=f"btx-{uuid.uuid4().hex}", bank_account_id=account.id,
            company_id=account.company_id, owner_id=account.owner_id,
            external_id=p.external_id, date=p.date, amount=money(p.amount),
            description=(p.description or "")[:255], category=category, status="NOVA",
        )
        db.add(tx)
        new.append(tx)

    reconciled = launched = 0
    if account.scope == "empresa":
        reconciled = await _auto_reconcile(db, account.company_id, new, u)
    else:
        for tx in new:
            entry = PersonalEntryModel(
                id=f"pes-{uuid.uuid4().hex[:10]}", owner_id=account.owner_id,
                type="RECEITA" if tx.amount > 0 else "DESPESA", amount=abs(tx.amount),
                description=tx.description, date=tx.date, category=tx.category or "Outros",
            )
            db.add(entry)
            tx.status, tx.entry_id = "LANCADA", entry.id
            launched += 1
    return {"imported": len(new), "duplicates": duplicates, "reconciled": reconciled, "launched": launched}


async def _auto_reconcile(db: AsyncSession, company_id: str, txs: list[BankTransactionModel], u: dict) -> int:
    """Marks a pending entry as paid only when exactly one candidate fits: same type and amount,
    due date within MATCH_WINDOW_DAYS. Anything ambiguous is left for a person to decide."""
    if not txs:
        return 0
    pending = list((await db.execute(
        select(FinancialEntryModel).where(FinancialEntryModel.company_id == company_id, FinancialEntryModel.status == "PENDENTE")
    )).scalars().all())
    taken: set[str] = set()
    count = 0
    for tx in txs:
        candidates = [e for e in pending if e.id not in taken and e.due_date and amounts_match(tx.amount, e)
                      and _days_between(e.due_date, tx.date) <= MATCH_WINDOW_DAYS]
        if len(candidates) != 1:
            continue
        entry = candidates[0]
        mark_paid(db, entry, tx, u, automatic=True)
        taken.add(entry.id)
        count += 1
    return count


def mark_paid(db: AsyncSession, entry: FinancialEntryModel, tx: BankTransactionModel, u: dict, automatic: bool) -> None:
    entry.status = "PAGO"
    entry.payment_date = tx.date
    tx.status, tx.entry_id = "CONCILIADA", entry.id
    audit.record_by(db, u, "CONCILIACAO_AUTOMATICA" if automatic else "CONCILIACAO_MANUAL",
                    entity="financial_entry", entity_id=entry.id,
                    details={"transacao": tx.id, "valor": tx.amount, "data": tx.date})



async def sync_from_provider(db: AsyncSession, account: BankAccountModel, provider, actor: dict) -> dict:
    """Pulls the aggregator's transactions since the last sync (3 days of overlap: late postings are
    caught and duplicates skipped). Raises ProviderError after marking the account. Caller commits."""
    from datetime import datetime, timedelta
    since = (date.fromisoformat(account.last_sync_at[:10]) - timedelta(days=3)) if account.last_sync_at else date.today() - timedelta(days=90)
    try:
        parsed = await provider.list_transactions(account.provider_account_id, since)
    except Exception:
        account.status = "ERRO"
        raise
    result = await ingest(db, account, parsed, actor)
    account.last_sync_at = datetime.utcnow().isoformat()
    account.status = "ATIVA"
    return result
