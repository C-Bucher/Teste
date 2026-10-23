# NOTA: Rota /jobs/daily: tarefa diária chamada por um agendador externo (exige o cabeçalho X-Cron-Secret).
#       Gera os alertas e sincroniza os bancos.

"""Scheduled work, called once a day by an external scheduler with X-Cron-Secret = CRON_SECRET."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.bank_hooks import _billing_allows, _check_secret, sync_all
from app.core.alerts import daily_alerts
from app.db.models import CompanyModel
from app.db.session import get_db
from app.integrations.bank.providers import BankProvider, get_bank_provider

router = APIRouter()


@router.post("/daily")
async def run_daily(request: Request, db: AsyncSession = Depends(get_db),
                    provider: BankProvider | None = Depends(get_bank_provider)):
    """Bank sync for every connected account, then due-date alerts for every company with access."""
    _check_secret(request, "x-cron-secret", "CRON_SECRET")
    bank = await sync_all(request, db, provider)
    alerts = 0
    for company_id in (await db.execute(select(CompanyModel.id))).scalars().all():
        if await _billing_allows(db, company_id):
            alerts += await daily_alerts(db, company_id)
            await db.commit()
    return {"bank": bank, "alerts_created": alerts}
