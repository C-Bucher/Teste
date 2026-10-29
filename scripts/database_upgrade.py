"""Check/apply revision 0011 from .env, without starting the app or seeding.

Default: read-only checks. Use --apply to upgrade in a PostgreSQL transaction.
Never prints connection details or individual database rows.
"""
import argparse
import asyncio
import importlib
import json
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[1]


def check(connection):
    if "alembic_version" not in inspect(connection).get_table_names():
        raise RuntimeError("Banco sem revisão Alembic: inspecione antes de aplicar.")
    revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    if revision not in {"0010", "0011"}:
        raise RuntimeError("A base precisa estar na revisão 0010 ou 0011.")
    migration = importlib.import_module("app.db.alembic.versions.0011_money_integrity_time_entries")
    migration.preflight(connection)
    counts = {}
    for table in ("financial_entries", "personal_entries", "kanban_cards", "active_timers"):
        counts[table] = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    return {"revision": revision, "preflight": "ok", "counts": counts}


def apply(connection, legacy_company=None):
    from app.db.session import _alembic_config
    from alembic import command

    if legacy_company:
        from scripts.legacy_database import adopt_legacy
        before = adopt_legacy(connection, legacy_company)
    else:
        before = check(connection)
    command.upgrade(_alembic_config(connection), "head")
    after = check(connection)
    for table, count in before["counts"].items():
        actual = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        if count != actual:
            raise RuntimeError("Contagens alteradas: atualização será revertida.")
    return {"before": before, "after": after}


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--legacy-company", help="empresa explicitamente confirmada para os registros sem proprietário")
    args = parser.parse_args()
    config = dotenv_values(ROOT / ".env")
    url = config.get("DATABASE_URL")
    if not url or "SUA_SENHA" in url or "<PROJECT_REF>" in url:
        raise RuntimeError("Configure DATABASE_URL no .env local.")
    if not url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("O comando espera PostgreSQL com asyncpg.")
    ssl = {} if config.get("DATABASE_SSL") == "disable" else {"ssl": "require"}
    engine = create_async_engine(url, connect_args=ssl, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SET LOCAL lock_timeout = '5s'"))
            await conn.execute(text("SET LOCAL statement_timeout = '120s'"))
            if args.legacy_company and not args.apply:
                from scripts.legacy_database import validate_legacy
                result = await conn.run_sync(lambda c: validate_legacy(c, args.legacy_company)[1])
            else:
                result = await conn.run_sync(lambda c: apply(c, args.legacy_company)) if args.apply else await conn.run_sync(check)
        report = json.dumps(result, indent=2, ensure_ascii=False)
        (ROOT / "docs/analise-banco/VERIFICACAO-SUPABASE.json").write_text(report, encoding="utf-8")
        print(report)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        if not (ROOT / ".env").is_file():
            raise RuntimeError("Configure DATABASE_URL no arquivo .env local; arquivo ainda não encontrado.")
        asyncio.run(main())
    except RuntimeError as exc:
        print(str(exc))
        raise SystemExit(1)
    except Exception as exc:
        print(f"Falha de conexão/execução ({type(exc).__name__}); credenciais omitidas.")
        raise SystemExit(1)
