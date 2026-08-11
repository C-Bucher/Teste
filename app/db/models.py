from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey, Text
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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    current_period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    subscription = relationship("SubscriptionModel", back_populates="invoices")

class EmployeeModel(Base):
    __tablename__ = "employees"

    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    contract_type = Column(String(50), default="CLT")
    base_salary = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    hire_date = Column(DateTime, default=datetime.utcnow)

    company = relationship("CompanyModel", back_populates="employees")
