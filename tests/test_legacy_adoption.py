"""Preserve two companies while adopting the inspected pre-Alembic schema."""
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.db.models import Base
from app.db.session import _alembic_config
from scripts.legacy_database import SCOPED, MISSING_TABLES, OPTIONAL_COLUMNS, baseline_metadata, adopt_legacy


def test_adoption_assigns_only_unowned_demo_rows_and_matches_current_models():
    baseline = baseline_metadata()
    legacy = sa.MetaData()
    removed = OPTIONAL_COLUMNS | {(table, "company_id") for table in SCOPED}
    for table in baseline.sorted_tables:
        if table.name in MISSING_TABLES:
            continue
        columns = [sa.Column(c.name, c.type, primary_key=c.primary_key,
                             nullable=True if (table.name, c.name) == ("employees", "company_id") else c.nullable)
                   for c in table.columns if (table.name, c.name) not in removed]
        sa.Table(table.name, legacy, *columns)
    for table in baseline.sorted_tables:
        if table.name not in legacy.tables:
            continue
        target = legacy.tables[table.name]
        for fk in table.foreign_key_constraints:
            if all(c.name in target.c for c in fk.columns):
                target.append_constraint(sa.ForeignKeyConstraint([c.name for c in fk.columns],
                    [e.target_fullname for e in fk.elements], name=fk.name, ondelete=fk.ondelete))
        for index in table.indexes:
            sa.Index(index.name, *[target.c[c.name] for c in index.columns], unique=index.unique)
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        legacy.create_all(conn)
        conn.execute(sa.text("INSERT INTO companies (id, name) VALUES ('demo', 'Demo'), ('acme', 'Acme')"))
        conn.execute(sa.text("INSERT INTO employees (id, full_name, email, role, company_id) VALUES ('old', 'Old', 'x@x', 'Dev', NULL), ('keep', 'Keep', 'y@y', 'Dev', 'acme')"))
        conn.execute(sa.text("INSERT INTO financial_entries (id, type, amount, status) VALUES ('f', 'RECEITA', 10, 'PENDENTE')"))
        before = adopt_legacy(conn, "demo")
        command.upgrade(_alembic_config(conn), "head")
        assert before["revision"] == "unversioned"
        assert conn.execute(sa.text("SELECT company_id FROM employees WHERE id = 'old'")).scalar() == "demo"
        assert conn.execute(sa.text("SELECT company_id FROM employees WHERE id = 'keep'")).scalar() == "acme"
        assert conn.execute(sa.text("SELECT company_id FROM financial_entries WHERE id = 'f'")).scalar() == "demo"
        assert conn.execute(sa.text("SELECT COUNT(*) FROM companies")).scalar() == 2
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []
