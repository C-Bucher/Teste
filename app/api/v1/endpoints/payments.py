from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.plans import PLANS_DB
from app.core.security import get_current_user
from app.db.models import CompanyModel, InvoiceModel, PlanModel, SubscriptionModel, UserModel
from app.db.session import get_db

router = APIRouter()

PLAN_PRICES = {
    plan["id"]: {
        "monthly": plan["price_monthly"],
        "yearly": plan["price_yearly"] * 12,
        "name": plan["name"],
        "data": plan,
    }
    for plan in PLANS_DB
}
DEFAULT_PLAN = next(plan for plan in PLANS_DB if plan["id"] == "plan-empresarial")


class CheckoutReq(BaseModel):
    plan_id: str
    billing_cycle: str
    payment_method: str
    card_number: Optional[str] = None
    card_name: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None
    company_name: Optional[str] = None
    cnpj_cpf: Optional[str] = None


def _subscription_dict(subscription: SubscriptionModel, plan_name: str, company_name: str) -> dict:
    return {
        "id": subscription.id,
        "company_name": company_name,
        "plan_id": subscription.plan_id,
        "plan_name": plan_name,
        "billing_cycle": subscription.billing_cycle,
        "amount": subscription.amount,
        "status": subscription.status,
        "payment_method": subscription.payment_method,
        "card_last4": subscription.card_last4,
        "card_brand": subscription.card_brand,
        "current_period_end": subscription.current_period_end,
        "auto_renew": subscription.auto_renew,
    }


async def _ensure_plan(db: AsyncSession, plan_data: dict) -> PlanModel:
    plan = await db.get(PlanModel, plan_data["id"])
    limits = plan_data.get("limits", {})
    if plan is None:
        plan = PlanModel(
            id=plan_data["id"],
            name=plan_data["name"],
            tagline=plan_data.get("tagline"),
            price_monthly=plan_data["price_monthly"],
            price_yearly=plan_data["price_yearly"],
            max_employees=limits.get("max_employees", 0),
            max_projects=limits.get("max_projects", 0),
            ai_cfo_unlimited=limits.get("ai_queries") == -1,
        )
        db.add(plan)
        await db.flush()
    return plan


@router.post("/checkout")
async def checkout(body: CheckoutReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.plan_id not in PLAN_PRICES:
        raise HTTPException(400, "Plano inválido")
    if body.billing_cycle not in {"monthly", "yearly"}:
        raise HTTPException(400, "Ciclo de cobrança inválido")
    if body.payment_method not in {"credit_card", "pix"}:
        raise HTTPException(400, "Forma de pagamento inválida")

    price_info = PLAN_PRICES[body.plan_id]
    await _ensure_plan(db, price_info["data"])
    amount = price_info[body.billing_cycle]
    current_subscriptions = (await db.execute(
        select(SubscriptionModel).where(
            SubscriptionModel.company_id == u["company_id"],
            SubscriptionModel.status == "ACTIVE",
        )
    )).scalars().all()
    for current_subscription in current_subscriptions:
        current_subscription.status = "REPLACED"
    subscription = SubscriptionModel(
        id=f"sub-{uuid.uuid4().hex[:10]}",
        company_id=u["company_id"],
        plan_id=body.plan_id,
        billing_cycle=body.billing_cycle,
        amount=amount,
        status="ACTIVE",
        payment_method=body.payment_method,
        card_last4=body.card_number[-4:] if body.card_number and len(body.card_number) >= 4 else None,
        card_brand="Visa" if body.payment_method == "credit_card" else None,
        auto_renew=True,
        current_period_end=(datetime.utcnow() + timedelta(days=365 if body.billing_cycle == "yearly" else 30)).isoformat(),
    )
    db.add(subscription)
    invoice = InvoiceModel(
        id=f"inv-{uuid.uuid4().hex[:10]}",
        subscription_id=subscription.id,
        amount=amount,
        status="PAID",
        description=f"Assinatura Plano {price_info['name']} ({'Anual' if body.billing_cycle == 'yearly' else 'Mensal'})",
        pdf_url=None,
    )
    db.add(invoice)
    company_users = (await db.execute(select(UserModel).where(UserModel.company_id == u["company_id"]))).scalars().all()
    for company_user in company_users:
        company_user.plan_scope = price_info["data"]["scope"]
    await db.commit()
    await db.refresh(subscription)
    await db.refresh(invoice)

    subscription_data = _subscription_dict(subscription, price_info["name"], body.company_name or "Sua Empresa")
    invoice_data = {
        "id": invoice.id,
        "subscription_id": invoice.subscription_id,
        "amount": invoice.amount,
        "status": invoice.status,
        "date": invoice.created_at,
        "pdf_url": invoice.pdf_url,
        "description": invoice.description,
    }
    return {
        "success": True,
        "message": f"Pagamento realizado com sucesso! Seu plano {price_info['name']} está ativo.",
        "subscription": subscription_data,
        "invoice": invoice_data,
        "pix_code": "PAGAMENTO-PIX-SIMULADO" if body.payment_method == "pix" else None,
        "plan_scope": price_info["data"]["scope"],
    }


@router.get("/subscription")
async def get_subscription(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SubscriptionModel)
        .where(SubscriptionModel.company_id == u["company_id"])
        .order_by(SubscriptionModel.created_at.desc())
    )
    subscription = result.scalars().first()
    if subscription is None:
        await _ensure_plan(db, DEFAULT_PLAN)
        subscription = SubscriptionModel(
            id=f"sub-{uuid.uuid4().hex[:10]}",
            company_id=u["company_id"],
            plan_id=DEFAULT_PLAN["id"],
            billing_cycle="monthly",
            amount=DEFAULT_PLAN["price_monthly"],
            status="ACTIVE",
            payment_method="credit_card",
            card_last4=None,
            card_brand=None,
            auto_renew=True,
            current_period_end=(datetime.utcnow() + timedelta(days=30)).isoformat(),
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
    plan = await db.get(PlanModel, subscription.plan_id)
    company = await db.get(CompanyModel, u["company_id"])
    return _subscription_dict(subscription, plan.name if plan else subscription.plan_id, company.name if company else "Sua Empresa")


@router.get("/invoices")
async def get_invoices(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvoiceModel)
        .join(SubscriptionModel, InvoiceModel.subscription_id == SubscriptionModel.id)
        .where(SubscriptionModel.company_id == u["company_id"])
        .order_by(InvoiceModel.created_at.desc())
    )
    return [
        {
            "id": invoice.id,
            "subscription_id": invoice.subscription_id,
            "amount": invoice.amount,
            "status": invoice.status,
            "date": invoice.created_at,
            "pdf_url": invoice.pdf_url,
            "description": invoice.description,
        }
        for invoice in result.scalars().all()
    ]
