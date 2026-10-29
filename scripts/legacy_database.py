"""Adopt the inspected pre-Alembic schema with an explicitly selected owner.

Build the historical baseline from revision 0001, never from today's ORM.
All writes use the caller's transaction. No users, companies or demo data are seeded.
"""
import sqlalchemy as sa
from alembic import command
from alembic.migration import MigrationContext
from alembic.operations import Operations

SCOPED = {"suppliers", "financial_entries", "clients", "projects", "notifications", "cost_centers", "categories", "export_logs"}
MISSING_TABLES = {"active_timers", "notification_preferences", "work_calendars"}
OPTIONAL_COLUMNS = {("notifications", "is_archived"), ("subscriptions", "card_brand"), ("subscriptions", "auto_renew")}


def baseline_metadata():
    from app.db.session import _alembic_config

    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    try:
        with engine.begin() as conn:
            command.upgrade(_alembic_config(conn), "0001")
            metadata.reflect(conn)
        metadata.remove(metadata.tables["alembic_version"])
        return metadata
    finally:
        engine.dispose()


def validate_legacy(connection, company_id):
    inspector = sa.inspect(connection)
    existing = set(inspector.get_table_names())
    if "alembic_version" in existing:
        raise RuntimeError("A adoção de legado só aceita banco sem revisão Alembic.")
    metadata = baseline_metadata()
    missing_tables = set(metadata.tables) - existing
    if missing_tables - MISSING_TABLES:
        raise RuntimeError("O esquema legado difere do formato inspecionado; interrompido.")
    allowed = OPTIONAL_COLUMNS | {(table, "company_id") for table in SCOPED}
    for table in existing & set(metadata.tables):
        actual = {c["name"]: c for c in inspector.get_columns(table)}
        for column in metadata.tables[table].columns:
            if column.name not in actual and (table, column.name) not in allowed:
                raise RuntimeError(f"Coluna inesperadamente ausente: {table}.{column.name}")
            if column.name in actual:
                old_type = actual[column.name]["type"]
                if old_type._type_affinity is not column.type._type_affinity:
                    raise RuntimeError(f"Tipo incompatível: {table}.{column.name}")
    if connection.execute(sa.text("SELECT COUNT(*) FROM companies WHERE id = :id"), {"id": company_id}).scalar() != 1:
        raise RuntimeError("Empresa de destino não encontrada.")
    counts = {table: connection.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()
              for table in sorted(existing & set(metadata.tables))}
    return metadata, {"revision": "unversioned", "legacy_owner": company_id, "counts": counts}


def adopt_legacy(connection, company_id):
    from app.db.session import _alembic_config

    metadata, before = validate_legacy(connection, company_id)
    op = Operations(MigrationContext.configure(connection))
    # Only the missing baseline tables are created, using the frozen old schema.
    metadata.create_all(connection, checkfirst=True)
    inspector = sa.inspect(connection)
    convention = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}
    for table in sorted(SCOPED | {"employees"}):
        columns = {c["name"]: c for c in inspector.get_columns(table)}
        if "company_id" not in columns:
            op.add_column(table, sa.Column("company_id", sa.String(50), nullable=True))
        connection.execute(sa.text(f"UPDATE {table} SET company_id = :company WHERE company_id IS NULL"), {"company": company_id})
        fks = inspector.get_foreign_keys(table)
        with op.batch_alter_table(table, naming_convention=convention) as batch:
            batch.alter_column("company_id", existing_type=sa.String(50), nullable=False)
            if not any(fk["constrained_columns"] == ["company_id"] for fk in fks):
                batch.create_foreign_key(f"fk_{table}_company_id_companies", "companies", ["company_id"], ["id"])
    for table, name in sorted(OPTIONAL_COLUMNS):
        if name not in {c["name"] for c in inspector.get_columns(table)}:
            op.add_column(table, metadata.tables[table].c[name]._copy())
            if name in {"is_archived", "auto_renew"}:
                value = "TRUE" if name == "auto_renew" else "FALSE"
                connection.execute(sa.text(f"UPDATE {table} SET {name} = {value}"))
    command.stamp(_alembic_config(connection), "0001")
    return before
