"""Read-only verification of revision 0011 on the configured PostgreSQL."""
import asyncio
import importlib
import json
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[1]


async def main():
    cfg = dotenv_values(ROOT / ".env")
    engine = create_async_engine(cfg["DATABASE_URL"], connect_args={"ssl": "require"}, echo=False)
    try:
        async with engine.connect() as conn:
            version = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar_one()
            assert version == "0011", "Revisão diferente de 0011"
            columns = {(r.table_name, r.column_name): r for r in (await conn.execute(text("""
                SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
                FROM information_schema.columns WHERE table_schema = 'public'
            """))).all()}
            migration = importlib.import_module("app.db.alembic.versions.0011_money_integrity_time_entries")
            checked = 0
            for table, fields in migration.MONEY_COLUMNS.items():
                for field, scale in fields.items():
                    column = columns[(table, field)]
                    assert (column.data_type, column.numeric_precision, column.numeric_scale) == ("numeric", 14, scale), f"Tipo incorreto: {table}.{field}"
                    checked += 1
            constraints = {r.conname: r.convalidated for r in (await conn.execute(text("""
                SELECT con.conname, con.convalidated FROM pg_constraint con
                JOIN pg_class t ON t.oid = con.conrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace WHERE n.nspname = 'public'
            """))).all()}
            expected = [name for checks in migration.CHECKS.values() for name in checks]
            expected += ["fk_financial_supplier_company", "uq_supplier_company_id",
                         "ck_time_entry_duration", "ck_time_entry_rate", "ck_time_entry_cost", "ck_time_entry_source"]
            assert all(constraints.get(name) for name in expected), "Restrição ausente ou não validada"
            mismatches = (await conn.execute(text("""
                SELECT COUNT(*) FROM kanban_cards c LEFT JOIN (
                    SELECT card_id, SUM(cost) AS cost, SUM(duration_seconds) AS seconds
                    FROM time_entries GROUP BY card_id
                ) t ON t.card_id = c.id
                WHERE COALESCE(c.cost_per_task, 0) <> COALESCE(t.cost, 0)
                   OR COALESCE(c.total_time_seconds, 0) <> COALESCE(t.seconds, 0)
            """))).scalar_one()
            assert mismatches == 0, "Acumulados do cartão divergem do histórico"
            ledger = [dict(r) for r in (await conn.execute(text("""
                SELECT source, COUNT(*) AS rows, SUM(duration_seconds) AS seconds, SUM(cost) AS cost
                FROM time_entries GROUP BY source
            """))).mappings()]
            tables = (await conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name <> 'alembic_version'"))).scalar_one()
            result = {"revision": version, "business_tables": tables, "numeric_columns_verified": checked,
                      "validated_constraints": len(expected), "history_mismatches": mismatches, "ledger": ledger}
        report = json.dumps(result, indent=2, default=str)
        (ROOT / "docs/analise-banco/VALIDACAO-SUPABASE.json").write_text(report, encoding="utf-8")
        print(report)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as exc:
        print(str(exc))
        raise SystemExit(1)
    except Exception as exc:
        print(f"Verificação falhou ({type(exc).__name__}); credenciais omitidas.")
        raise SystemExit(1)
