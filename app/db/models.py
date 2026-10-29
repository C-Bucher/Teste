# NOTA: Define todas as tabelas do banco (41 ao todo) como classes SQLAlchemy: empresas, usuários, assinaturas, colaboradores,
#       lançamentos, Kanban, Hub Pessoal, bancos, IA, auditoria e outras. Mudou uma tabela aqui? Crie também uma migração.

from sqlalchemy import Column, String, Float, Numeric, Boolean, Integer, ForeignKey, ForeignKeyConstraint, CheckConstraint, Text, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class CompanyModel(Base):
    __tablename__ = "companies"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    fiscal_year_start = Column(Integer, default=1)
    onboarding_completed = Column(Boolean, default=False)
    permissions_customized = Column(Boolean, default=False)
    billing_customer_id = Column(String(100), nullable=True)   # customer id at the payment provider

    users = relationship("UserModel", back_populates="company")
    subscriptions = relationship("SubscriptionModel", back_populates="company")
    employees = relationship("EmployeeModel", back_populates="company")

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="FUNCIONARIO")
    plan_scope = Column(String(20), default="completo")
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    failed_login_count = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(String(50), nullable=True)
    mfa_secret = Column(String(255), nullable=True)          # TOTP seed, encrypted (app/core/crypto.py)
    mfa_recovery_codes = Column(Text, nullable=True)         # JSON list of SHA-256 hashes, each usable once
    terms_version = Column(String(20), nullable=True)        # version of terms + privacy policy accepted (app/core/legal.py)
    terms_accepted_at = Column(String(50), nullable=True)

    company = relationship("CompanyModel", back_populates="users")

class PlanModel(Base):
    __tablename__ = "plans"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    tagline = Column(String(255), nullable=True)
    price_monthly = Column(Numeric(14, 2), nullable=False)
    price_yearly = Column(Numeric(14, 2), nullable=False)
    max_employees = Column(Integer, default=5)
    max_projects = Column(Integer, default=3)
    ai_cfo_unlimited = Column(Boolean, default=False)

    subscriptions = relationship("SubscriptionModel", back_populates="plan")

class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    plan_id = Column(String(50), ForeignKey("plans.id"), nullable=False)
    billing_cycle = Column(String(20), default="monthly")
    amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(50), default="ACTIVE")
    payment_method = Column(String(50), default="credit_card")
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(30), nullable=True)
    auto_renew = Column(Boolean, default=True)
    current_period_end = Column(String(50), nullable=False)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    provider = Column(String(30), nullable=True)                    # asaas | simulado | None (trial/legacy)
    provider_subscription_id = Column(String(100), nullable=True, index=True)
    trial_ends_at = Column(String(50), nullable=True)
    canceled_at = Column(String(50), nullable=True)

    company = relationship("CompanyModel", back_populates="subscriptions")
    plan = relationship("PlanModel", back_populates="subscriptions")
    invoices = relationship("InvoiceModel", back_populates="subscription")

class InvoiceModel(Base):
    __tablename__ = "invoices"

    id = Column(String(50), primary_key=True)
    subscription_id = Column(String(50), ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(50), default="PAID")
    description = Column(String(255), nullable=True)
    pdf_url = Column(String(255), nullable=True)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    provider_payment_id = Column(String(100), nullable=True, unique=True, index=True)  # named unique index
    due_date = Column(String(20), nullable=True)
    paid_at = Column(String(50), nullable=True)
    payment_url = Column(String(500), nullable=True)                # provider-hosted page (Pix/boleto/card)
    billing_type = Column(String(20), nullable=True)

    subscription = relationship("SubscriptionModel", back_populates="invoices")

class EmployeeModel(Base):
    __tablename__ = "employees"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    contract_type = Column(String(50), default="CLT")
    base_salary = Column(Numeric(14, 2), default=0.0)
    is_active = Column(Boolean, default=True)
    hire_date = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    cpf = Column(String(20), nullable=True)
    position = Column(String(100), nullable=True)
    ctc_snapshot = Column(Numeric(14, 2), nullable=True)
    ctc_monthly = Column(Numeric(14, 2), nullable=True)
    hourly_rate = Column(Numeric(14, 4), nullable=True)
    hourly_cost = Column(Numeric(14, 4), nullable=True)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)

    company = relationship("CompanyModel", back_populates="employees")


class SalaryHistoryModel(Base):
    __tablename__ = "salary_history"

    id = Column(String(50), primary_key=True)
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
    base_salary = Column(Numeric(14, 2), nullable=True)
    ctc_monthly = Column(Numeric(14, 2), nullable=True)
    ctc_snapshot = Column(Numeric(14, 2), nullable=True)
    changed_at = Column(String(20), nullable=True)
    reason = Column(String(255), nullable=True)


class SupplierModel(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("company_id", "id", name="uq_supplier_company_id"),)

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cnpj_cpf = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    email = Column(String(255), nullable=True)


class FinancialEntryModel(Base):
    __tablename__ = "financial_entries"
    __table_args__ = (
        CheckConstraint("amount > 0 AND amount < 1000000000000", name="ck_financial_amount"),
        CheckConstraint("type IN ('RECEITA', 'DESPESA')", name="ck_financial_type"),
        CheckConstraint("status IN ('PENDENTE', 'PAGO')", name="ck_financial_status"),
        ForeignKeyConstraint(["company_id", "supplier_id"], ["suppliers.company_id", "suppliers.id"], name="fk_financial_supplier_company"),
    )

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    type = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(String(20), nullable=True)
    payment_date = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="PENDENTE")
    category = Column(String(100), nullable=True)
    supplier_id = Column(String(50), nullable=True)
    cost_center = Column(String(100), nullable=True)
    attachment_name = Column(String(255), nullable=True)   # original file name shown to the user
    attachment_key = Column(String(255), nullable=True)    # private storage key, never returned by the API


class ClientModel(Base):
    __tablename__ = "clients"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    cnpj = Column(String(20), nullable=True)
    contact_name = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    segment = Column(String(100), nullable=True)
    status = Column(String(20), default="ATIVO")


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    status = Column(String(50), default="PLANEJAMENTO")
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)


class KanbanColumnModel(Base):
    __tablename__ = "kanban_columns"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    order = Column(Integer, default=0)


class KanbanCardModel(Base):
    __tablename__ = "kanban_cards"

    id = Column(String(50), primary_key=True)
    column_id = Column(String(50), ForeignKey("kanban_columns.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    assignee = Column(String(255), nullable=True)
    assignee_id = Column(String(50), nullable=True)
    cost_per_task = Column(Numeric(14, 2), default=0.0)
    total_time_seconds = Column(Integer, default=0)
    status = Column(String(50), default="ABERTO")
    priority = Column(String(20), default="MEDIA")
    due_date = Column(String(20), nullable=True)


class CardCommentModel(Base):
    __tablename__ = "card_comments"

    id = Column(String(50), primary_key=True)
    card_id = Column(String(50), ForeignKey("kanban_cards.id"), nullable=False)
    author = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(String(50), nullable=True)


class NotificationModel(Base):
    __tablename__ = "notifications"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String(255), nullable=True)
    type = Column(String(20), default="INFO")
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(String(50), nullable=True)


class CostCenterModel(Base):
    __tablename__ = "cost_centers"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True)


class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=True)


class PersonalEntryModel(Base):
    __tablename__ = "personal_entries"
    __table_args__ = (
        CheckConstraint("amount > 0 AND amount < 1000000000000", name="ck_personal_amount"),
        CheckConstraint("type IN ('RECEITA', 'DESPESA')", name="ck_personal_type"),
    )

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(255), nullable=True)
    date = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)


class PersonalCategoryModel(Base):
    __tablename__ = "personal_categories"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=True)


class ExportLogModel(Base):
    __tablename__ = "export_logs"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    type = Column(String(50), nullable=True)
    format = Column(String(20), nullable=True)
    status = Column(String(20), default="PRONTO")
    created_at = Column(String(50), nullable=True)
    size_bytes = Column(Integer, nullable=True)


class PersonalAccountModel(Base):
    __tablename__ = "personal_accounts"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=True)
    balance = Column(Numeric(14, 2), default=0.0)
    limit = Column(Numeric(14, 2), nullable=True)
    closing_day = Column(Integer, nullable=True)
    due_day = Column(Integer, nullable=True)


class PersonalBudgetModel(Base):
    __tablename__ = "personal_budgets"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    category = Column(String(100), nullable=True)
    limit_amount = Column(Numeric(14, 2), nullable=True)
    spent_amount = Column(Numeric(14, 2), default=0.0)


class PersonalGoalModel(Base):
    __tablename__ = "personal_goals"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    target_amount = Column(Numeric(14, 2), nullable=True)
    current_amount = Column(Numeric(14, 2), default=0.0)
    target_date = Column(String(20), nullable=True)


class PersonalDebtModel(Base):
    __tablename__ = "personal_debts"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    total_amount = Column(Numeric(14, 2), nullable=True)
    remaining_amount = Column(Numeric(14, 2), nullable=True)
    installments_total = Column(Integer, nullable=True)
    installments_paid = Column(Integer, default=0)
    interest_rate = Column(Float, nullable=True)


class PersonalSubscriptionModel(Base):
    __tablename__ = "personal_subscriptions"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(14, 2), nullable=True)
    billing_day = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)


class PersonalSplitModel(Base):
    __tablename__ = "personal_splits"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    description = Column(String(255), nullable=True)
    total_amount = Column(Numeric(14, 2), nullable=False)
    participants = Column(JSON, nullable=False, default=list)


class PersonalTimeboxModel(Base):
    __tablename__ = "personal_timeboxes"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    start_time = Column(String(20), nullable=True)
    end_time = Column(String(20), nullable=True)


class PersonalOkrModel(Base):
    __tablename__ = "personal_okrs"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    objective = Column(String(255), nullable=True)
    key_results = Column(JSON, nullable=False, default=list)


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)        # GERENTE | FUNCIONARIO (ADMIN nunca é gravado aqui)
    module_key = Column(String(50), nullable=False)  # ver MODULES em app/core/permissions.py


class WorkCalendarModel(Base):
    __tablename__ = "work_calendars"

    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    work_days = Column(JSON, nullable=False, default=lambda: [1, 2, 3, 4, 5])
    work_hours_per_day = Column(Float, nullable=False, default=8.0)
    holidays = Column(JSON, nullable=False, default=list)


class NotificationPreferenceModel(Base):
    __tablename__ = "notification_preferences"

    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    inapp_enabled = Column(Boolean, nullable=False, default=True)


class ActiveTimerModel(Base):
    __tablename__ = "active_timers"

    card_id = Column(String(50), ForeignKey("kanban_cards.id", ondelete="CASCADE"), primary_key=True)
    employee_id = Column(String(50), nullable=True)
    timer_id = Column(String(50), nullable=False)
    started_at = Column(String(50), nullable=False)
    hourly_rate = Column(Numeric(14, 4), nullable=False, default=85)
    actor_id = Column(String(50), nullable=True)


class TimeEntryModel(Base):
    """Immutable rate/cost snapshot for one completed timer (or legacy total)."""
    __tablename__ = "time_entries"
    __table_args__ = (
        CheckConstraint("duration_seconds >= 0", name="ck_time_entry_duration"),
        CheckConstraint("hourly_rate >= 0", name="ck_time_entry_rate"),
        CheckConstraint("cost >= 0", name="ck_time_entry_cost"),
        CheckConstraint("source IN ('timer', 'legacy')", name="ck_time_entry_source"),
    )
    id = Column(String(50), primary_key=True)
    card_id = Column(String(50), ForeignKey("kanban_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(String(50), nullable=True)  # historical identity, retained after staff deletion
    actor_id = Column(String(50), nullable=True)
    started_at = Column(String(50), nullable=True)
    ended_at = Column(String(50), nullable=True)
    duration_seconds = Column(Integer, nullable=False)
    hourly_rate = Column(Numeric(14, 4), nullable=False)
    cost = Column(Numeric(14, 2), nullable=False)
    source = Column(String(20), nullable=False, default="timer")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(50), nullable=True)          # no FK: the trail must outlive deleted users
    action = Column(String(50), nullable=False)
    entity = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)                # JSON-encoded
    ip = Column(String(64), nullable=True)
    created_at = Column(String(50), nullable=False, default=lambda: datetime.utcnow().isoformat(), index=True)


class CtcParamsModel(Base):
    """Per-company multipliers for the employee total cost (CTC = base salary x multiplier)."""
    __tablename__ = "ctc_params"

    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    clt_multiplier = Column(Float, nullable=False, default=1.75)
    pj_multiplier = Column(Float, nullable=False, default=1.10)
    estagio_multiplier = Column(Float, nullable=False, default=1.10)
    monthly_hours = Column(Float, nullable=False, default=176.0)


class BankAccountModel(Base):
    """A bank account fed by file import or by an Open Finance aggregator.
    Business accounts carry company_id; Hub Pessoal accounts carry owner_id (never both)."""
    __tablename__ = "bank_accounts"
    __table_args__ = (
        CheckConstraint("(scope = 'empresa' AND company_id IS NOT NULL AND owner_id IS NULL) OR (scope = 'pessoal' AND owner_id IS NOT NULL AND company_id IS NULL)", name="ck_bank_account_owner"),
    )

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    scope = Column(String(20), nullable=False)            # empresa | pessoal
    name = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=True)
    source = Column(String(20), nullable=False, default="arquivo")   # arquivo | agregador
    provider = Column(String(30), nullable=True)
    provider_item_id = Column(String(100), nullable=True)
    provider_account_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="ATIVA")
    last_sync_at = Column(String(50), nullable=True)
    created_at = Column(String(50), nullable=False, default=lambda: datetime.utcnow().isoformat())


class BankTransactionModel(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (UniqueConstraint("bank_account_id", "external_id", name="uq_bank_tx_external"),)

    id = Column(String(50), primary_key=True)
    bank_account_id = Column(String(50), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    external_id = Column(String(100), nullable=False)
    date = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)                 # + money in, - money out
    description = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="NOVA")   # NOVA | CONCILIADA | LANCADA | IGNORADA
    entry_id = Column(String(50), nullable=True)           # financial_entries.id or personal_entries.id
    created_at = Column(String(50), nullable=False, default=lambda: datetime.utcnow().isoformat())


class CategorizationRuleModel(Base):
    """"If the bank description contains <pattern>, use <category>"."""
    __tablename__ = "categorization_rules"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    pattern = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)


class AiMessageModel(Base):
    """Chat history of the CFO assistants (one row per message)."""
    __tablename__ = "ai_messages"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)          # user | assistant
    content = Column(Text, nullable=False)
    source = Column(String(20), nullable=True)         # ia | regra
    model = Column(String(60), nullable=True)
    created_at = Column(String(50), nullable=False, default=lambda: datetime.utcnow().isoformat(), index=True)


class AiUsageModel(Base):
    """Real model calls per company per month, checked against the plan's ai_queries (LIM-1)."""
    __tablename__ = "ai_usage"
    __table_args__ = (UniqueConstraint("company_id", "period", name="uq_ai_usage_period"),)

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String(7), nullable=False)          # YYYY-MM
    count = Column(Integer, nullable=False, default=0)


class PasswordResetModel(Base):
    """One-time password recovery link (AUTH-3). Only the SHA-256 of the token is stored."""
    __tablename__ = "password_resets"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(String(50), nullable=False)
    used_at = Column(String(50), nullable=True)
    created_at = Column(String(50), nullable=False, default=lambda: datetime.utcnow().isoformat())
