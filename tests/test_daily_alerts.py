# NOTA: Testa o job diário: avisa contas a vencer, recebíveis atrasados e prazos do Kanban, uma vez por dia.

"""NOT-2: the daily job warns about bills due soon, late receivables and Kanban deadlines, once a day."""

from datetime import date, datetime, timedelta

from sqlalchemy import update

from app.core import mailer
from app.db.models import SubscriptionModel
from app.db.session import async_session_maker
from tests.conftest import register_admin


def _d(days):
    return (date.today() + timedelta(days=days)).isoformat()


async def _notes(client, acc):
    r = (await client.get("/notifications/", headers=acc["headers"])).json()
    return r if isinstance(r, list) else r.get("items", [])


async def test_daily_job_creates_each_alert_once(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "segredo-cron")
    acc = await register_admin(client, plan="plan-empresarial")
    h = acc["headers"]
    await client.post("/financial/entries", headers=h, json={"type": "DESPESA", "amount": 300, "description": "Aluguel", "due_date": _d(2)})
    await client.post("/financial/entries", headers=h, json={"type": "DESPESA", "amount": 50, "description": "Longe", "due_date": _d(20)})
    await client.post("/financial/entries", headers=h, json={"type": "RECEITA", "amount": 800, "description": "Cliente X", "due_date": _d(-4)})
    proj = (await client.post("/kanban/projects", headers=h, json={"name": "Site"})).json()
    col = (await client.get(f"/kanban/projects/{proj['id']}/board", headers=h)).json()["columns"][0]["id"]
    await client.post("/kanban/cards", headers=h, json={"title": "Entregar layout", "column_id": col, "due_date": _d(1)})

    assert (await client.post("/jobs/daily", headers={"x-cron-secret": "errado"})).status_code == 401
    mailer.OUTBOX.clear()
    r = await client.post("/jobs/daily", headers={"x-cron-secret": "segredo-cron"})
    assert r.status_code == 200, r.text

    titles = [n["title"] for n in await _notes(client, acc)]
    assert any(t.startswith("Contas a pagar nos próximos 3 dias") for t in titles)
    assert any(t.startswith("Recebimentos atrasados") for t in titles)
    assert any(t.startswith("Tarefas com prazo próximo") for t in titles)
    bills = next(n for n in await _notes(client, acc) if n["title"].startswith("Contas a pagar"))
    assert "R$ 300,00" in bills["message"] and "Longe" not in bills["message"]
    assert any(m["to"] == acc["email"] for m in mailer.OUTBOX)

    before = len(await _notes(client, acc))
    await client.post("/jobs/daily", headers={"x-cron-secret": "segredo-cron"})
    assert len(await _notes(client, acc)) == before, "same alert is not repeated on the same day"


async def test_daily_job_skips_blocked_companies(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "segredo-cron")
    acc = await register_admin(client, plan="plan-empresarial")
    await client.post("/financial/entries", headers=acc["headers"], json={"type": "DESPESA", "amount": 10, "due_date": _d(1)})
    async with async_session_maker() as s:
        await s.execute(update(SubscriptionModel).where(SubscriptionModel.company_id == acc["user"]["company_id"])
                        .values(trial_ends_at=(datetime.utcnow() - timedelta(days=1)).isoformat()))
        await s.commit()
    await client.post("/jobs/daily", headers={"x-cron-secret": "segredo-cron"})
    titles = [n["title"] for n in await _notes(client, acc)]
    assert not any(t.startswith("Contas a pagar") for t in titles)
