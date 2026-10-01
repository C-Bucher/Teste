import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base
from app.db.migrations import run_compatibility_migrations

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Absolute path so the SQLite file does not depend on the directory uvicorn was started from (DB-1).
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite+aiosqlite:///{(PROJECT_ROOT / 'techconnect.db').as_posix()}"

BASELINE_REVISION = "0001"
# Tables introduced after the baseline; a pre-Alembic database must not get them from create_all.
# Pre-Alembic databases always have `users`, so post-baseline columns on it are added by their revision.
POST_BASELINE_TABLES = {"audit_logs", "ctc_params", "bank_accounts", "bank_transactions", "categorization_rules",
                        "ai_messages", "ai_usage"}

engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
if "postgresql" in DATABASE_URL:
    # Supabase requires TLS; a local Postgres container usually has none (DATABASE_SSL=disable).
    if os.getenv("DATABASE_SSL", "require") != "disable":
        engine_kwargs["connect_args"] = {"ssl": "require"}
else:
    engine_kwargs["pool_recycle"] = 280

engine = create_async_engine(DATABASE_URL, **engine_kwargs)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session_maker() as session:
        yield session


def _alembic_config(connection):
    from alembic.config import Config

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.attributes["connection"] = connection
    return cfg


def _migrate(connection) -> None:
    from alembic import command

    tables = set(inspect(connection).get_table_names())
    cfg = _alembic_config(connection)
    if tables and "alembic_version" not in tables:
        # Database created by the old create_all path: bring it to the baseline, then version it.
        baseline_tables = [t for t in Base.metadata.sorted_tables if t.name not in POST_BASELINE_TABLES]
        Base.metadata.create_all(connection, tables=baseline_tables)
        run_compatibility_migrations(connection)
        command.stamp(cfg, BASELINE_REVISION)
    command.upgrade(cfg, "head")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(_migrate)
