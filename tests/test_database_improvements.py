"""Regression tests for revision 0011: decimal, DB invariants and cost history."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.core.money import money
from app.db import session as db_session
from app.db.models import EmployeeModel, FinancialEntryModel, TimeEntryModel
from app.db.session import async_session_maker


async def _entry(client, account, **changes):
    response = await client.post("/financial/entries", headers=account["headers"],
                                 json={"type": "RECEITA", "amount": "0.10", **changes})
    assert response.status_code == 200, response.text
    return response.json()


def test_decimal_rounding_is_explicit_and_rejects_nonfinite_values():
    assert money("1.005") == Decimal("1.01")
    assert money("0.10") + money("0.20") == Decimal("0.30")
    for value in ("NaN", "Infinity", "-Infinity", "1000000000000"):
        with pytest.raises(ValueError):
            money(value)


async def test_decimal_values_survive_persistence_and_financial_summary(client, company_a):
    first = await _entry(client, company_a, due_date="2026-10-01")
    second = await _entry(client, company_a, amount="0.20", due_date="2026-10-01")
    async with async_session_maker() as db:
        values = [(await db.get(FinancialEntryModel, row["id"])).amount for row in (first, second)]
        assert all(isinstance(value, Decimal) for value in values)
        assert sum(values) == Decimal("0.30")
    result = await client.get("/financial/dre", headers=company_a["headers"],
                              params={"start": "2026-10-01", "end": "2026-10-31"})
    assert result.status_code == 200
    assert result.json()["total_receitas"] == 0.30


@pytest.mark.parametrize("changes", [
    {"amount": -1}, {"amount": 0}, {"amount": "NaN"}, {"amount": "Infinity"},
    {"amount": "999999999999.999"}, {"type": "INVALIDO"}, {"status": "INVALIDO"},
])
async def test_updates_cannot_bypass_financial_validation(client, company_a, changes):
    row = await _entry(client, company_a)
    response = await client.put(f"/financial/entries/{row['id']}", headers=company_a["headers"], json=changes)
    assert response.status_code == 400
    unchanged = (await client.get(f"/financial/entries/{row['id']}", headers=company_a["headers"])).json()
    assert unchanged["amount"] == 0.1 and unchanged["type"] == "RECEITA" and unchanged["status"] == "PENDENTE"


@pytest.mark.parametrize("column,value", [("amount", -1), ("type", "INVALIDO"), ("status", "INVALIDO")])
async def test_database_rejects_invalid_financial_writes_without_the_api(client, company_a, column, value):
    row = await _entry(client, company_a)
    async with async_session_maker() as db:
        with pytest.raises(IntegrityError):
            await db.execute(text(f"UPDATE financial_entries SET {column} = :value WHERE id = :id"),
                             {"value": value, "id": row["id"]})
            await db.commit()
        await db.rollback()


async def test_database_rejects_bank_account_with_two_owners(company_a):
    async with async_session_maker() as db:
        with pytest.raises(IntegrityError):
            await db.execute(text("""INSERT INTO bank_accounts
                (id, company_id, owner_id, scope, name, source, status)
                VALUES ('invalid-owner', :company, :owner, 'empresa', 'X', 'arquivo', 'ATIVA')"""),
                {"company": company_a["user"]["company_id"], "owner": company_a["user"]["id"]})
            await db.commit()
        await db.rollback()


async def test_supplier_company_fk_rejects_direct_cross_company_link_and_delete_preserves_entry(client, company_a, company_b):
    supplier = (await client.post("/suppliers/", headers=company_b["headers"], json={"name": "B"})).json()
    row = await _entry(client, company_a)
    async with async_session_maker() as db:
        with pytest.raises(IntegrityError):
            await db.execute(text("UPDATE financial_entries SET supplier_id = :supplier WHERE id = :id"),
                             {"supplier": supplier["id"], "id": row["id"]})
            await db.commit()
        await db.rollback()
    own = (await client.post("/suppliers/", headers=company_a["headers"], json={"name": "A"})).json()
    linked = await _entry(client, company_a, supplier_id=own["id"])
    assert (await client.delete(f"/suppliers/{own['id']}", headers=company_a["headers"])).status_code == 200
    result = (await client.get(f"/financial/entries/{linked['id']}", headers=company_a["headers"])).json()
    assert result["supplier_id"] is None and result["amount"] == 0.1


async def _card(client, account, employee_id=None):
    h = account["headers"]
    project = (await client.post("/kanban/projects", headers=h, json={"name": "History"})).json()
    board = (await client.get(f"/kanban/projects/{project['id']}/board", headers=h)).json()
    response = await client.post("/kanban/cards", headers=h,
                                 json={"title": "Task", "column_id": board["columns"][0]["id"], "assignee_id": employee_id})
    assert response.status_code == 200, response.text
    return response.json()


async def test_timer_preserves_each_rate_and_old_cost_when_salary_changes(client, company_a, company_b, monkeypatch):
    from app.api.v1.endpoints import kanban

    now = [datetime(2026, 10, 28, 12, tzinfo=timezone.utc)]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now[0]

    monkeypatch.setattr(kanban, "datetime", Clock)
    h = company_a["headers"]
    employee = (await client.post("/employees/", headers=h,
        json={"full_name": "Dev", "email": "history@example.com", "base_salary": 1000, "role": "Dev"})).json()
    async with async_session_maker() as db:
        (await db.get(EmployeeModel, employee["id"])).hourly_rate = Decimal("50")
        await db.commit()
    card = await _card(client, company_a, employee["id"])
    path = f"/kanban/cards/{card['id']}"
    assert (await client.post(path + "/timer/start", headers=h)).status_code == 200
    # A rate change during a running session must not change its captured rate.
    async with async_session_maker() as db:
        (await db.get(EmployeeModel, employee["id"])).hourly_rate = Decimal("60")
        await db.commit()
    now[0] += timedelta(hours=2)
    first = await client.post(path + "/timer/stop", headers=h)
    assert first.status_code == 200, first.text
    assert first.json()["cost_per_task"] == 100
    assert (await client.post(path + "/timer/start", headers=h)).status_code == 200
    now[0] += timedelta(hours=1)
    second = await client.post(path + "/timer/stop", headers=h)
    assert second.status_code == 200, second.text
    assert second.json()["cost_per_task"] == 160 and second.json()["total_time_seconds"] == 10800
    assert (await client.post(path + "/timer/stop", headers=h)).status_code == 409
    entries = (await client.get(path + "/time-entries", headers=h)).json()["items"]
    assert [(e["hourly_rate"], e["cost"]) for e in entries] == [(50, 100), (60, 60)]
    assert all(e["actor_id"] == company_a["user"]["id"] and e["source"] == "timer" for e in entries)
    assert (await client.get(path + "/time-entries", headers=company_b["headers"])).status_code == 404
    # A normal card edit cannot overwrite historical totals.
    edit = await client.put(path, headers=h, json={"cost_per_task": 1, "total_time_seconds": 1})
    assert edit.json()["cost_per_task"] == 160 and edit.json()["total_time_seconds"] == 10800
    assert (await client.delete(path, headers=h)).status_code == 200
    async with async_session_maker() as db:
        assert (await db.execute(select(TimeEntryModel).where(TimeEntryModel.card_id == card["id"]))).scalars().all() == []


def _legacy_database(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "legacy.db").as_posix())
    with engine.begin() as conn:
        command.upgrade(db_session._alembic_config(conn), "0010")
        conn.execute(text("INSERT INTO companies (id, name) VALUES ('c', 'Legacy')"))
        conn.execute(text("INSERT INTO projects (id, company_id, name) VALUES ('p', 'c', 'P')"))
        conn.execute(text("INSERT INTO kanban_columns (id, project_id, name) VALUES ('k', 'p', 'K')"))
        conn.execute(text("INSERT INTO kanban_cards (id, column_id, title, total_time_seconds, cost_per_task) VALUES ('t', 'k', 'T', 7200, 100)"))
    return engine


def test_migration_preserves_legacy_totals_and_runs_only_once(tmp_path):
    engine = _legacy_database(tmp_path)
    with engine.begin() as conn:
        command.upgrade(db_session._alembic_config(conn), "head")
        command.upgrade(db_session._alembic_config(conn), "head")
        entry = conn.execute(text("SELECT * FROM time_entries")).mappings().one()
        assert entry["source"] == "legacy" and entry["cost"] == 100 and entry["duration_seconds"] == 7200
        assert entry["started_at"] is None and entry["ended_at"] is None
        card = conn.execute(text("SELECT cost_per_task, total_time_seconds FROM kanban_cards")).one()
        assert tuple(card) == (100, 7200)


def test_migration_aborts_on_invalid_existing_rows_before_changing_structure(tmp_path):
    engine = _legacy_database(tmp_path)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO financial_entries (id, company_id, type, amount, status) VALUES ('bad', 'c', 'RECEITA', -10, 'PENDENTE')"))
    with engine.begin() as conn:
        with pytest.raises(RuntimeError, match="preflight failed"):
            command.upgrade(db_session._alembic_config(conn), "head")
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0010"
        assert "time_entries" not in inspect(conn).get_table_names()


async def test_fresh_demo_seed_includes_legacy_history_and_is_idempotent(tmp_path, monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.db import seed
    from app.db.models import KanbanCardModel

    engine = create_async_engine("sqlite+aiosqlite:///" + (tmp_path / "demo.db").as_posix())
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(db_session._migrate)
        monkeypatch.setattr(seed, "async_session_maker", maker)
        await seed.seed_if_empty()
        await seed.seed_if_empty()
        async with maker() as db:
            entries = (await db.execute(select(TimeEntryModel))).scalars().all()
            cards = (await db.execute(select(KanbanCardModel))).scalars().all()
            expected = [c for c in cards if (c.total_time_seconds or 0) > 0 or (c.cost_per_task or 0) > 0]
            assert entries and len(entries) == len(expected)
            for entry in entries:
                card = next(c for c in cards if c.id == entry.card_id)
                assert entry.source == "legacy" and entry.cost == card.cost_per_task
    finally:
        await engine.dispose()
