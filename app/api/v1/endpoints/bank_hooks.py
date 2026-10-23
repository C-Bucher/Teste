# NOTA: Rotas de máquina para máquina: webhook do Pluggy e /sync-all (sincroniza todas as contas, chamado pelo agendador).

"""Machine-to-machine bank routes: the aggregator's webhook and the scheduler's daily sync.
Not behind a user session nor the subscription gate; each is authenticated by its own secret."""

import hmac
import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import billing
from app.db.models import BankAccountModel, UserModel
from app.db.session import get_db
from app.integrations.bank import service
from app.integrations.bank.providers import BankProvider, ProviderError, get_bank_provider

router = APIRouter()
log = logging.getLogger("techconnect.bank")


def _check_secret(request: Request, header: str, env: str) -> None:
    expected = os.getenv(env, "")
    if not expected or not hmac.compare_digest(request.headers.get(header, ""), expected):
        raise HTTPException(401, "Segredo inválido")


async def _company_of(db: AsyncSession, account: BankAccountModel) -> str | None:
    if account.company_id:
        return account.company_id
    owner = await db.get(UserModel, account.owner_id) if account.owner_id else None
    return owner.company_id if owner else None


async def _billing_allows(db: AsyncSession, company_id: str | None) -> bool:
    """No aggregator calls (they cost money) for companies whose subscription is inactive."""
    if not company_id:
        return False
    now = datetime.utcnow()
    for sub in await billing.live_subscriptions(db, company_id):
        if await billing.grants_access(db, sub, now):
            return True
    return False


async def _sync(db: AsyncSession, accounts: list[BankAccountModel], provider: BankProvider) -> int:
    synced = 0
    for account in accounts:
        company_id = await _company_of(db, account)
        if not await _billing_allows(db, company_id):
            continue
        actor = {"company_id": account.company_id or company_id, "id": None}
        try:
            await service.sync_from_provider(db, account, provider, actor)
            synced += 1
        except ProviderError as e:
            log.warning("Falha ao sincronizar a conta %s: %s", account.id, e)
        await db.commit()
    return synced


@router.post("/webhook/pluggy")
async def pluggy_webhook(request: Request, db: AsyncSession = Depends(get_db),
                         provider: BankProvider | None = Depends(get_bank_provider)):
    """Configure in the Pluggy dashboard with the header X-Webhook-Secret = PLUGGY_WEBHOOK_SECRET."""
    _check_secret(request, "x-webhook-secret", "PLUGGY_WEBHOOK_SECRET")
    payload = await request.json()
    item_id = payload.get("itemId") or (payload.get("item") or {}).get("id")
    if provider is None or not item_id:
        return {"received": True, "synced_accounts": 0}
    accounts = list((await db.execute(select(BankAccountModel).where(
        BankAccountModel.provider_item_id == item_id, BankAccountModel.source == "agregador"))).scalars().all())
    return {"received": True, "synced_accounts": await _sync(db, accounts, provider)}


@router.post("/sync-all")
async def sync_all(request: Request, db: AsyncSession = Depends(get_db),
                   provider: BankProvider | None = Depends(get_bank_provider)):
    """Called by an external scheduler (e.g. daily), header X-Cron-Secret = CRON_SECRET.
    Syncs every aggregator account not refreshed in the last 12 hours."""
    _check_secret(request, "x-cron-secret", "CRON_SECRET")
    if provider is None:
        return {"synced_accounts": 0, "reason": "agregador não configurado"}
    cutoff = (datetime.utcnow() - timedelta(hours=12)).isoformat()
    accounts = list((await db.execute(select(BankAccountModel).where(
        BankAccountModel.source == "agregador",
        (BankAccountModel.last_sync_at.is_(None)) | (BankAccountModel.last_sync_at < cutoff),
    ))).scalars().all())
    return {"synced_accounts": await _sync(db, accounts, provider), "candidates": len(accounts)}
