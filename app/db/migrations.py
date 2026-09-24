"""Small, idempotent compatibility migrations for pre-Alembic databases.

New installations are created from SQLAlchemy metadata. Existing installations
need these additive columns before the ORM can query the affected tables.
"""

from sqlalchemy import inspect, text


COMPANY_SCOPED_TABLES = (
    "suppliers",
    "financial_entries",
    "clients",
    "projects",
    "notifications",
    "cost_centers",
    "categories",
    "export_logs",
)


def _column_names(connection, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(connection).get_columns(table_name)}


def run_compatibility_migrations(connection) -> None:
    tables = set(inspect(connection).get_table_names())
    for table_name in COMPANY_SCOPED_TABLES:
        if table_name not in tables:
            continue
        columns = _column_names(connection, table_name)
        if "company_id" not in columns:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN company_id VARCHAR(50)"))
        connection.execute(
            text(f"UPDATE {table_name} SET company_id = :company_id WHERE company_id IS NULL"),
            {"company_id": "cmp-001"},
        )

    if "notifications" in tables and "is_archived" not in _column_names(connection, "notifications"):
        connection.execute(text("ALTER TABLE notifications ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"))

    if "subscriptions" in tables:
        subscription_columns = _column_names(connection, "subscriptions")
        if "card_brand" not in subscription_columns:
            connection.execute(text("ALTER TABLE subscriptions ADD COLUMN card_brand VARCHAR(30)"))
        if "auto_renew" not in subscription_columns:
            connection.execute(text("ALTER TABLE subscriptions ADD COLUMN auto_renew BOOLEAN DEFAULT TRUE"))
