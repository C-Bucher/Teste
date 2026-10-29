# NOTA: Testa que as datas da demonstração avançam até hoje sem perder a distância entre elas.

"""SEED-1: the demo company's dates move forward to today, keeping the gaps between them."""

import os
import tempfile
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


async def test_refresh_moves_demo_dates_by_elapsed_days():
    from app.db import session as db_session
    from app.db.demo_dates import refresh_demo_dates
    from app.db.models import CompanyModel, FinancialEntryModel
    from app.db.seed import DEMO_COMPANY_ID

    path = os.path.join(tempfile.mkdtemp(prefix="tc-demo-"), "demo.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
    async with engine.begin() as conn:
        await conn.run_sync(db_session._migrate)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    seeded_on = date.today() - timedelta(days=40)
    async with maker() as s:
        s.add(CompanyModel(id=DEMO_COMPANY_ID, name="Demo", created_at=f"{seeded_on.isoformat()}T10:00:00"))
        await s.flush()
        s.add(FinancialEntryModel(id="fin-a", company_id=DEMO_COMPANY_ID, type="DESPESA", amount=1, due_date=(seeded_on + timedelta(days=15)).isoformat()))
        s.add(FinancialEntryModel(id="fin-b", company_id=DEMO_COMPANY_ID, type="RECEITA", amount=1, due_date=(seeded_on - timedelta(days=5)).isoformat(),
                                  payment_date=(seeded_on - timedelta(days=3)).isoformat()))
        await s.commit()

    async with maker() as s:
        assert await refresh_demo_dates(s) == 40
        a = await s.get(FinancialEntryModel, "fin-a")
        b = await s.get(FinancialEntryModel, "fin-b")
        assert a.due_date == (date.today() + timedelta(days=15)).isoformat()
        assert b.due_date == (date.today() - timedelta(days=5)).isoformat()
        assert b.payment_date == (date.today() - timedelta(days=3)).isoformat()
    async with maker() as s:
        assert await refresh_demo_dates(s) == 0, "running twice the same day changes nothing"
    await engine.dispose()
