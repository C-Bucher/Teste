"""Keeps the demo data current (SEED-1).

The seed writes dates relative to the day it ran; months later "due in 15 days" is long past.
This shifts every date of the demo company and demo user by the days elapsed since the last
refresh, keeping the gaps between them. Run: `python -m app.db.demo_dates`, or set
DEMO_REFRESH_DATES=1 to do it at startup. Only rows of cmp-001 / usr-001 are touched.
"""

import asyncio
import re
from datetime import date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base, CompanyModel
from app.db.seed import DEMO_COMPANY_ID, DEMO_USER_ID

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")
# Bookkeeping columns that record when a row was written, not business dates.
_SKIP = {"created_at", "terms_accepted_at", "locked_until", "last_sync_at", "expires_at", "used_at", "canceled_at", "current_period_end"}


def _shift(value: str, days: int) -> str:
    head = value[:10]
    return (date.fromisoformat(head) + timedelta(days=days)).isoformat() + value[10:]


async def refresh_demo_dates(db: AsyncSession) -> int:
    company = await db.get(CompanyModel, DEMO_COMPANY_ID)
    if company is None or not company.created_at:
        return 0
    days = (date.today() - date.fromisoformat(company.created_at[:10])).days
    if days <= 0:
        return 0
    for table in Base.metadata.sorted_tables:
        owner_col = table.c.get("company_id") if "company_id" in table.c else table.c.get("owner_id") if "owner_id" in table.c else None
        if owner_col is None or table.name in ("companies", "users", "subscriptions", "invoices"):
            continue
        owner_id = DEMO_COMPANY_ID if owner_col.name == "company_id" else DEMO_USER_ID
        date_cols = [c for c in table.c if (c.name == "date" or c.name.endswith("_date") or c.name.endswith("_at")) and c.name not in _SKIP]
        if not date_cols:
            continue
        pk = list(table.primary_key.columns)[0]
        rows = (await db.execute(select(pk, *date_cols).where(owner_col == owner_id))).all()
        for row in rows:
            values = {c.name: _shift(row[i + 1], days) for i, c in enumerate(date_cols) if isinstance(row[i + 1], str) and _ISO.match(row[i + 1])}
            if values:
                await db.execute(update(table).where(pk == row[0]).values(**values))
    company.created_at = datetime.utcnow().isoformat()
    await db.commit()
    return days


async def _main() -> None:
    from app.db.session import async_session_maker, init_db
    await init_db()
    async with async_session_maker() as db:
        days = await refresh_demo_dates(db)
    print(f"Datas da demonstração avançadas em {days} dia(s)." if days else "Datas da demonstração já estão atualizadas.")


if __name__ == "__main__":
    asyncio.run(_main())
