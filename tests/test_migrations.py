"""DB-3: schema is versioned by Alembic and stays in sync with the ORM models."""

import os
import tempfile

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.db import session as db_session
from app.db.models import Base


def _head():
    return ScriptDirectory.from_config(db_session._alembic_config(None)).get_current_head()


def _fresh_sqlite():
    path = os.path.join(tempfile.mkdtemp(prefix="tc-mig-"), "db.sqlite")
    return create_engine(f"sqlite:///{path}")


def test_empty_database_is_built_by_migrations_and_matches_models():
    engine = _fresh_sqlite()
    with engine.begin() as conn:
        db_session._migrate(conn)
    with engine.connect() as conn:
        assert conn.execute(text("select version_num from alembic_version")).scalar() == _head()
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], f"models and migrations diverged — create a new Alembic revision: {diff}"


def test_pre_alembic_database_is_stamped_and_upgraded():
    engine = _fresh_sqlite()
    legacy_tables = [t for t in Base.metadata.sorted_tables if t.name not in db_session.POST_BASELINE_TABLES]
    with engine.begin() as conn:
        # old create_all path, missing a column that the compatibility migration adds
        Base.metadata.create_all(conn, tables=legacy_tables)
        conn.execute(text("insert into companies (id, name) values ('cmp-001', 'Demo')"))
    with engine.begin() as conn:
        db_session._migrate(conn)
    with engine.connect() as conn:
        assert conn.execute(text("select version_num from alembic_version")).scalar() == _head()
        assert set(t.name for t in Base.metadata.sorted_tables) <= set(inspect(conn).get_table_names())
        assert conn.execute(text("select count(*) from companies")).scalar() == 1


def test_migrating_twice_is_a_no_op():
    engine = _fresh_sqlite()
    with engine.begin() as conn:
        db_session._migrate(conn)
    with engine.begin() as conn:
        db_session._migrate(conn)
