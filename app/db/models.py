from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, Text, JSON
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

    company = relationship("CompanyModel", back_populates="users")

class PlanModel(Base):
    __tablename__ = "plans"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    tagline = Column(String(255), nullable=True)
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
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
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="ACTIVE")
    payment_method = Column(String(50), default="credit_card")
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(30), nullable=True)
    auto_renew = Column(Boolean, default=True)
    current_period_end = Column(String(50), nullable=False)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())

    company = relationship("CompanyModel", back_populates="subscriptions")
    plan = relationship("PlanModel", back_populates="subscriptions")
    invoices = relationship("InvoiceModel", back_populates="subscription")

class InvoiceModel(Base):
    __tablename__ = "invoices"

    id = Column(String(50), primary_key=True)
    subscription_id = Column(String(50), ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="PAID")
    description = Column(String(255), nullable=True)
    pdf_url = Column(String(255), nullable=True)
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())

    subscription = relationship("SubscriptionModel", back_populates="invoices")

class EmployeeModel(Base):
    __tablename__ = "employees"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    contract_type = Column(String(50), default="CLT")
    base_salary = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    hire_date = Column(String(50), default=lambda: datetime.utcnow().isoformat())
    cpf = Column(String(20), nullable=True)
    position = Column(String(100), nullable=True)
    ctc_snapshot = Column(Float, nullable=True)
    ctc_monthly = Column(Float, nullable=True)
    hourly_rate = Column(Float, nullable=True)
    hourly_cost = Column(Float, nullable=True)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)

    company = relationship("CompanyModel", back_populates="employees")


class SalaryHistoryModel(Base):
    __tablename__ = "salary_history"

    id = Column(String(50), primary_key=True)
    employee_id = Column(String(50), ForeignKey("employees.id"), nullable=False)
    base_salary = Column(Float, nullable=True)
    ctc_monthly = Column(Float, nullable=True)
    ctc_snapshot = Column(Float, nullable=True)
    changed_at = Column(String(20), nullable=True)
    reason = Column(String(255), nullable=True)


class SupplierModel(Base):
    __tablename__ = "suppliers"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cnpj_cpf = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    email = Column(String(255), nullable=True)


class FinancialEntryModel(Base):
    __tablename__ = "financial_entries"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=False)
    type = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    due_date = Column(String(20), nullable=True)
    payment_date = Column(String(20), nullable=True)
    status = Column(String(20), default="PENDENTE")
    category = Column(String(100), nullable=True)
    supplier_id = Column(String(50), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
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
    cost_per_task = Column(Float, default=0.0)
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

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
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
    balance = Column(Float, default=0.0)
    limit = Column(Float, nullable=True)
    closing_day = Column(Integer, nullable=True)
    due_day = Column(Integer, nullable=True)


class PersonalBudgetModel(Base):
    __tablename__ = "personal_budgets"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    category = Column(String(100), nullable=True)
    limit_amount = Column(Float, nullable=True)
    spent_amount = Column(Float, default=0.0)


class PersonalGoalModel(Base):
    __tablename__ = "personal_goals"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    target_amount = Column(Float, nullable=True)
    current_amount = Column(Float, default=0.0)
    target_date = Column(String(20), nullable=True)


class PersonalDebtModel(Base):
    __tablename__ = "personal_debts"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    total_amount = Column(Float, nullable=True)
    remaining_amount = Column(Float, nullable=True)
    installments_total = Column(Integer, nullable=True)
    installments_paid = Column(Integer, default=0)
    interest_rate = Column(Float, nullable=True)


class PersonalSubscriptionModel(Base):
    __tablename__ = "personal_subscriptions"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=True)
    billing_day = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)


class PersonalSplitModel(Base):
    __tablename__ = "personal_splits"

    id = Column(String(50), primary_key=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    description = Column(String(255), nullable=True)
    total_amount = Column(Float, nullable=False)
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
