"""Alembic environment.

Two entry points:
- the app calls `upgrade` at startup and hands over a live sync connection via
  `config.attributes["connection"]` (see app/db/session.py::init_db);
- the CLI (`alembic upgrade head`, `alembic revision --autogenerate`) builds its own
  async engine from DATABASE_URL.
"""

import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models import Base
from app.db.session import DATABASE_URL

config = context.config
target_metadata = Base.metadata


def _configure(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=connection.dialect.name == "sqlite",
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(_configure)
    await engine.dispose()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _configure(connection)
    else:
        asyncio.run(_run_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
