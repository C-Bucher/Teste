"""Read-only schema inventory for a legacy database, without printing credentials."""
import asyncio
import json
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[1]


def inventory(connection):
    inspector = inspect(connection)
    result = {}
    for table in inspector.get_table_names(schema="public"):
        columns = [{"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
                   for c in inspector.get_columns(table, schema="public")]
        result[table] = {"columns": columns,
                         "foreign_keys": inspector.get_foreign_keys(table, schema="public"),
                         "unique": inspector.get_unique_constraints(table, schema="public"),
                         "checks": inspector.get_check_constraints(table, schema="public")}
    return result


async def main():
    config = dotenv_values(ROOT / ".env")
    engine = create_async_engine(config["DATABASE_URL"], connect_args={"ssl": "require"}, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.run_sync(inventory)
            ownership = (await conn.execute(text("SELECT (SELECT COUNT(*) FROM companies) AS companies, (SELECT COUNT(*) FROM employees WHERE company_id IS NULL) AS employees_without_company, (SELECT COUNT(DISTINCT company_id) FROM users) AS user_companies"))).mappings().one()
        (ROOT / "docs/analise-banco/SCHEMA-SUPABASE-ANTES.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(json.dumps({table: [c["name"] for c in info["columns"]] for table, info in result.items()}, indent=2))
        print(json.dumps(dict(ownership)))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Inspeção falhou ({type(exc).__name__}); credenciais omitidas.")
        raise SystemExit(1)
