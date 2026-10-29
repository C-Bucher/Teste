"""Exact monetary columns, financial invariants and historical time entries.

Existing invalid rows abort the migration before DDL; no business data is deleted.
Legacy card totals are carried forward without inventing individual time sessions.
"""
from decimal import Decimal, ROUND_HALF_UP
import uuid

from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

MONEY_COLUMNS = {'plans': {'price_monthly': 2, 'price_yearly': 2}, 'employees': {'base_salary': 2, 'ctc_snapshot': 2, 'ctc_monthly': 2, 'hourly_rate': 4, 'hourly_cost': 4}, 'subscriptions': {'amount': 2}, 'financial_entries': {'amount': 2}, 'invoices': {'amount': 2}, 'personal_accounts': {'balance': 2, 'limit': 2}, 'personal_budgets': {'limit_amount': 2, 'spent_amount': 2}, 'personal_debts': {'total_amount': 2, 'remaining_amount': 2}, 'personal_entries': {'amount': 2}, 'personal_goals': {'target_amount': 2, 'current_amount': 2}, 'personal_splits': {'total_amount': 2}, 'personal_subscriptions': {'amount': 2}, 'salary_history': {'base_salary': 2, 'ctc_monthly': 2, 'ctc_snapshot': 2}, 'bank_transactions': {'amount': 2}, 'kanban_cards': {'cost_per_task': 2}}

CHECKS = {
    "financial_entries": {
        "ck_financial_amount": "amount > 0 AND amount < 1000000000000",
        "ck_financial_type": "type IN ('RECEITA', 'DESPESA')",
        "ck_financial_status": "status IN ('PENDENTE', 'PAGO')",
    },
    "personal_entries": {
        "ck_personal_amount": "amount > 0 AND amount < 1000000000000",
        "ck_personal_type": "type IN ('RECEITA', 'DESPESA')",
    },
    "bank_accounts": {
        "ck_bank_account_owner": "(scope = 'empresa' AND company_id IS NOT NULL AND owner_id IS NULL) OR (scope = 'pessoal' AND owner_id IS NOT NULL AND company_id IS NULL)",
    },
}


def preflight(connection):
    problems = []
    for table, checks in CHECKS.items():
        for name, rule in checks.items():
            count = connection.execute(sa.text(f"SELECT COUNT(*) FROM {table} WHERE NOT ({rule}) OR ({rule}) IS NULL")).scalar()
            if count:
                problems.append(f"{name}: {count} invalid rows")
    mismatched = connection.execute(sa.text("""
        SELECT COUNT(*) FROM financial_entries f LEFT JOIN suppliers s
        ON s.id = f.supplier_id AND s.company_id = f.company_id
        WHERE f.supplier_id IS NOT NULL AND s.id IS NULL
    """)).scalar()
    if mismatched:
        problems.append(f"supplier/company mismatch: {mismatched}")
    invalid_cards = connection.execute(sa.text("SELECT COUNT(*) FROM kanban_cards WHERE total_time_seconds < 0 OR cost_per_task < 0")).scalar()
    if invalid_cards:
        problems.append(f"negative legacy card totals: {invalid_cards}")
    for table, columns in MONEY_COLUMNS.items():
        for column, scale in columns.items():
            limit = 10 ** (14 - scale)
            quoted = connection.dialect.identifier_preparer.quote(column)
            rounded = f"ROUND(CAST({quoted} AS NUMERIC), {scale})" if connection.dialect.name == "postgresql" else f"ROUND({quoted}, {scale})"
            count = connection.execute(sa.text(f"SELECT COUNT(*) FROM {table} WHERE {quoted} IS NOT NULL AND NOT ({rounded} > -{limit} AND {rounded} < {limit})")).scalar()
            if count:
                problems.append(f"{table}.{column} out of numeric range: {count}")
    if problems:
        raise RuntimeError("Migration 0011 preflight failed; review existing data first: " + "; ".join(problems))


def upgrade():
    connection = op.get_bind()
    preflight(connection)
    dialect = connection.dialect.name
    # Freeze the list here so future ORM edits never change a historical revision.
    for table, columns in MONEY_COLUMNS.items():
        with op.batch_alter_table(table) as batch:
            for column, scale in columns.items():
                quoted = connection.dialect.identifier_preparer.quote(column)
                batch.alter_column(column, existing_type=sa.Float(), type_=sa.Numeric(14, scale),
                                   postgresql_using=f"round({quoted}::numeric, {scale})")
        if dialect == "sqlite":
            for column, scale in columns.items():
                quoted = connection.dialect.identifier_preparer.quote(column)
                op.execute(sa.text(f"UPDATE {table} SET {quoted} = ROUND({quoted}, {scale}) WHERE {quoted} IS NOT NULL"))

    with op.batch_alter_table("suppliers") as batch:
        batch.create_unique_constraint("uq_supplier_company_id", ["company_id", "id"])
    convention = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}
    supplier_fk = next(fk for fk in sa.inspect(connection).get_foreign_keys("financial_entries") if fk["constrained_columns"] == ["supplier_id"])
    with op.batch_alter_table("financial_entries", naming_convention=convention) as batch:
        batch.drop_constraint(supplier_fk["name"] or "fk_financial_entries_supplier_id_suppliers", type_="foreignkey")
        batch.create_foreign_key("fk_financial_supplier_company", "suppliers", ["company_id", "supplier_id"], ["company_id", "id"])
        batch.alter_column("status", existing_type=sa.String(20), nullable=False)
    for table, checks in CHECKS.items():
        with op.batch_alter_table(table) as batch:
            for name, rule in checks.items():
                batch.create_check_constraint(name, rule)

    with op.batch_alter_table("active_timers") as batch:
        batch.add_column(sa.Column("hourly_rate", sa.Numeric(14, 4), nullable=False, server_default="85"))
        batch.add_column(sa.Column("actor_id", sa.String(50), nullable=True))
    # Snapshot the current valid employee rate for timers already running.
    connection.execute(sa.text("""
        UPDATE active_timers SET hourly_rate = COALESCE((
            SELECT e.hourly_rate FROM employees e
            JOIN kanban_cards c ON c.id = active_timers.card_id
            JOIN kanban_columns k ON k.id = c.column_id
            JOIN projects p ON p.id = k.project_id
            WHERE e.id = active_timers.employee_id AND e.company_id = p.company_id
        ), 85)
    """))
    with op.batch_alter_table("active_timers") as batch:
        batch.alter_column("hourly_rate", existing_type=sa.Numeric(14, 4), server_default=None)

    op.create_table("time_entries",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("card_id", sa.String(50), sa.ForeignKey("kanban_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.String(50), nullable=True),
        sa.Column("actor_id", sa.String(50), nullable=True),
        sa.Column("started_at", sa.String(50), nullable=True),
        sa.Column("ended_at", sa.String(50), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(14, 4), nullable=False),
        sa.Column("cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_time_entry_duration"),
        sa.CheckConstraint("hourly_rate >= 0", name="ck_time_entry_rate"),
        sa.CheckConstraint("cost >= 0", name="ck_time_entry_cost"),
        sa.CheckConstraint("source IN ('timer', 'legacy')", name="ck_time_entry_source"),
    )
    op.create_index("ix_time_entries_card_id", "time_entries", ["card_id"])
    entries = sa.table("time_entries", sa.column("id"), sa.column("card_id"), sa.column("employee_id"),
                       sa.column("duration_seconds"), sa.column("hourly_rate", sa.Numeric(14,4)),
                       sa.column("cost", sa.Numeric(14,2)), sa.column("source"))
    cards = connection.execute(sa.text("SELECT id, assignee_id, total_time_seconds, cost_per_task FROM kanban_cards WHERE total_time_seconds > 0 OR cost_per_task > 0")).mappings().all()
    for card in cards:
        seconds = card["total_time_seconds"] or 0
        cost = Decimal(str(card["cost_per_task"] or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # A legacy rate is an implied average, never represented as a real session.
        rate = (cost * 3600 / seconds).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if seconds else Decimal(0)
        connection.execute(entries.insert().values(id="legacy-" + uuid.uuid4().hex, card_id=card["id"],
                           employee_id=card["assignee_id"], duration_seconds=seconds, hourly_rate=rate,
                           cost=cost, source="legacy"))


def downgrade():
    # Downgrade intentionally discards individual time-entry history; card totals remain.
    op.drop_table("time_entries")
    with op.batch_alter_table("active_timers") as batch:
        batch.drop_column("actor_id")
        batch.drop_column("hourly_rate")
    for table, checks in reversed(list(CHECKS.items())):
        with op.batch_alter_table(table) as batch:
            for name in checks:
                batch.drop_constraint(name, type_="check")
    with op.batch_alter_table("financial_entries") as batch:
        batch.drop_constraint("fk_financial_supplier_company", type_="foreignkey")
        batch.create_foreign_key("fk_financial_entries_supplier_id_suppliers", "suppliers", ["supplier_id"], ["id"], ondelete="SET NULL")
        batch.alter_column("status", existing_type=sa.String(20), nullable=True)
    with op.batch_alter_table("suppliers") as batch:
        batch.drop_constraint("uq_supplier_company_id", type_="unique")
    for table, columns in reversed(list(MONEY_COLUMNS.items())):
        with op.batch_alter_table(table) as batch:
            for column, scale in columns.items():
                batch.alter_column(column, existing_type=sa.Numeric(14, scale), type_=sa.Float())
