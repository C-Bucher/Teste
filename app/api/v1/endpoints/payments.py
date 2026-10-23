# NOTA: Rotas /payments: abre o checkout no Asaas, recebe o webhook de confirmação, consulta assinatura, acesso,
#       faturas e uso, e cancela a assinatura.

"""Subscription billing (PAY-1): checkout through the payment provider, the provider's webhook,
the company's subscription/invoices and cancellation. Access rules live in app/core/billing.py."""

import hmac
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit, billing
from app.core.notify import notify_company
from app.core.security import get_current_user
from app.db.models import CompanyModel, InvoiceModel, SubscriptionModel
from app.db.session import get_db
from app.integrations.payments.providers import PaymentProvider, PaymentProviderError, get_payment_provider

router = APIRouter()

PLAN_PRICES = {
    plan["id"]: {"monthly": plan["price_monthly"], "yearly": round(plan["price_yearly"] * 12, 2), "name": plan["name"], "data": plan}
    for plan in billing.PLANS_DB
}
BILLING_TYPES = {"pix": "PIX", "boleto": "BOLETO", "credit_card": "CREDIT_CARD"}
PROVIDER_CYCLES = {"monthly": "MONTHLY", "yearly": "YEARLY"}


def _require_admin(u: dict) -> None:
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente o administrador da empresa gerencia a assinatura")


def _invoice_dict(inv: InvoiceModel) -> dict:
    return {"id": inv.id, "subscription_id": inv.subscription_id, "amount": inv.amount, "status": inv.status,
            "date": inv.created_at, "due_date": inv.due_date, "paid_at": inv.paid_at, "payment_url": inv.payment_url,
            "pdf_url": inv.pdf_url, "description": inv.description}


async def _subscription_dict(db: AsyncSession, sub: SubscriptionModel, company: CompanyModel | None, allowed: bool | None = None) -> dict:
    plan = PLAN_PRICES.get(sub.plan_id, {}).get("data") or {}
    pending = (await db.execute(
        select(InvoiceModel).where(InvoiceModel.subscription_id == sub.id, InvoiceModel.status.in_(("PENDING", "OVERDUE")))
        .order_by(InvoiceModel.due_date)
    )).scalars().first()
    return {
        "id": sub.id, "company_name": company.name if company else "", "plan_id": sub.plan_id, "plan_name": plan.get("name", sub.plan_id),
        "billing_cycle": sub.billing_cycle, "amount": sub.amount, "status": sub.status, "payment_method": sub.payment_method,
        "provider": sub.provider, "trial_ends_at": sub.trial_ends_at, "current_period_end": sub.current_period_end,
        "canceled_at": sub.canceled_at, "auto_renew": sub.auto_renew,
        "pending_payment_url": pending.payment_url if pending else None,
        **({"access": {"allowed": allowed}} if allowed is not None else {}),
    }


# ---------- checkout ----------

class CheckoutReq(BaseModel):
    plan_id: str
    billing_cycle: str
    payment_method: str
    cnpj_cpf: Optional[str] = None
    company_name: Optional[str] = None


@router.post("/checkout")
async def checkout(body: CheckoutReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db),
                   provider: PaymentProvider | None = Depends(get_payment_provider)):
    _require_admin(u)
    if body.plan_id not in PLAN_PRICES:
        raise HTTPException(400, "Plano inválido")
    if body.billing_cycle not in PROVIDER_CYCLES:
        raise HTTPException(400, "Ciclo de cobrança inválido")
    if body.payment_method not in BILLING_TYPES:
        raise HTTPException(400, "Forma de pagamento inválida. Use pix, boleto ou credit_card")
    if provider is None:
        raise HTTPException(503, "Pagamentos ainda não estão configurados. Fale com o suporte")

    price = PLAN_PRICES[body.plan_id]
    amount = price[body.billing_cycle]
    company = await db.get(CompanyModel, u["company_id"])
    document = re.sub(r"\D", "", body.cnpj_cpf or (company.cnpj if company else "") or "")
    if provider.name != "simulado" and len(document) not in (11, 14):
        raise HTTPException(400, "Informe um CPF ou CNPJ válido: ele é exigido para emitir a cobrança")
    await billing.ensure_plan_row(db, price["data"])

    sub = SubscriptionModel(
        id=f"sub-{uuid.uuid4().hex[:10]}", company_id=u["company_id"], plan_id=body.plan_id, billing_cycle=body.billing_cycle,
        amount=amount, status="PENDING", payment_method=body.payment_method, auto_renew=True, provider=provider.name,
        current_period_end=datetime.utcnow().isoformat(),
    )
    db.add(sub)
    await db.flush()
    try:
        customer_id = await provider.ensure_customer(
            company_id=u["company_id"], name=body.company_name or (company.name if company else u["full_name"]),
            email=u["email"], cpf_cnpj=document, existing_id=company.billing_customer_id if company else None)
        provider_sub_id, first = await provider.create_subscription(
            customer_id=customer_id, value=amount, cycle=PROVIDER_CYCLES[body.billing_cycle],
            billing_type=BILLING_TYPES[body.payment_method],
            description=f"TechConnect {price['name']} ({'anual' if body.billing_cycle == 'yearly' else 'mensal'})",
            external_reference=sub.id)
    except PaymentProviderError as e:
        await db.rollback()
        raise HTTPException(502, str(e))
    if company:
        company.billing_customer_id = customer_id
        if document and not company.cnpj:
            company.cnpj = document
    sub.provider_subscription_id = provider_sub_id
    description = f"Assinatura Plano {price['name']} ({'Anual' if body.billing_cycle == 'yearly' else 'Mensal'})"

    if provider.name == "simulado":
        # Development only: paid on the spot.
        invoice = InvoiceModel(id=f"inv-{uuid.uuid4().hex[:10]}", subscription_id=sub.id, amount=amount, status="PAID",
                               description=description, due_date=datetime.utcnow().date().isoformat(), paid_at=datetime.utcnow().isoformat())
        db.add(invoice)
        await _activate(db, sub, invoice, provider)
    else:
        invoice = InvoiceModel(id=f"inv-{uuid.uuid4().hex[:10]}", subscription_id=sub.id, amount=amount, status="PENDING",
                               description=description, provider_payment_id=first.id if first else None,
                               due_date=first.due_date if first else None, payment_url=first.invoice_url if first else None,
                               billing_type=BILLING_TYPES[body.payment_method])
        db.add(invoice)
    audit.record_by(db, u, "CHECKOUT", entity="subscription", entity_id=sub.id,
                    details={"plano": body.plan_id, "ciclo": body.billing_cycle, "forma": body.payment_method, "valor": amount, "provedor": provider.name})
    await db.commit()
    return {
        "success": True, "provider": provider.name,
        "message": "Assinatura ativa." if sub.status == "ACTIVE" else "Assinatura criada. Conclua o pagamento para ativar o plano.",
        "subscription": await _subscription_dict(db, sub, company), "invoice": _invoice_dict(invoice),
        "payment_url": invoice.payment_url, "plan_scope": price["data"]["scope"],
    }


async def _activate(db: AsyncSession, sub: SubscriptionModel, invoice: InvoiceModel, provider: PaymentProvider | None) -> None:
    """A confirmed payment: the subscription becomes the company's plan for one more cycle."""
    now = datetime.utcnow()
    start = max(now, datetime.fromisoformat(sub.current_period_end)) if sub.status in ("ACTIVE", "PAST_DUE") else now
    sub.current_period_end = (start + timedelta(days=billing.CYCLE_DAYS.get(sub.billing_cycle, 30))).isoformat()
    sub.status = "ACTIVE"
    invoice.status = "PAID"
    invoice.paid_at = invoice.paid_at or now.isoformat()
    await billing.apply_plan_scope(db, sub.company_id, sub.plan_id)
    for other in await billing.live_subscriptions(db, sub.company_id):
        if other.id != sub.id and other.status != "CANCELED":
            other.status = "REPLACED"
            if other.provider_subscription_id and provider is not None and other.provider == provider.name:
                try:
                    await provider.cancel_subscription(other.provider_subscription_id)
                except PaymentProviderError:
                    pass  # the old one stays open at the provider; here it is no longer used


# ---------- provider webhook ----------

@router.post("/webhook/asaas")
async def asaas_webhook(request: Request, db: AsyncSession = Depends(get_db),
                        provider: PaymentProvider | None = Depends(get_payment_provider)):
    """Asaas calls this for every charge event. Authenticated by the token set in the Asaas panel."""
    expected = os.getenv("ASAAS_WEBHOOK_TOKEN", "")
    if not expected or not hmac.compare_digest(request.headers.get("asaas-access-token", ""), expected):
        raise HTTPException(401, "Token do webhook inválido")
    payload = await request.json()
    event, p = payload.get("event", ""), payload.get("payment") or {}
    sub = (await db.execute(select(SubscriptionModel).where(SubscriptionModel.provider_subscription_id == p.get("subscription")))).scalar_one_or_none() \
        if p.get("subscription") else None
    if not sub or not p.get("id"):
        return {"received": True, "ignored": True}

    invoice = (await db.execute(select(InvoiceModel).where(InvoiceModel.provider_payment_id == p["id"]))).scalar_one_or_none()
    if invoice is None:
        # A renewal charge, or the first one when it was not known at checkout time.
        invoice = (await db.execute(select(InvoiceModel).where(InvoiceModel.subscription_id == sub.id, InvoiceModel.provider_payment_id.is_(None),
                                                               InvoiceModel.status == "PENDING"))).scalars().first()
        if invoice is None:
            invoice = InvoiceModel(id=f"inv-{uuid.uuid4().hex[:10]}", subscription_id=sub.id, amount=float(p.get("value") or sub.amount),
                                   status="PENDING", description=f"Renovação {PLAN_PRICES.get(sub.plan_id, {}).get('name', '')}".strip())
            db.add(invoice)
        invoice.provider_payment_id = p["id"]
    invoice.due_date = p.get("dueDate") or invoice.due_date
    invoice.payment_url = p.get("invoiceUrl") or invoice.payment_url

    if event in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
        if invoice.status != "PAID":
            await _activate(db, sub, invoice, provider)
            await notify_company(db, sub.company_id, "Pagamento confirmado",
                                 f"Recebemos o pagamento de R$ {invoice.amount:.2f}. Plano ativo até {sub.current_period_end[:10]}.", kind="SUCCESS")
    elif event == "PAYMENT_OVERDUE":
        invoice.status = "OVERDUE"
        if sub.status == "ACTIVE":
            sub.status = "PAST_DUE"
        await notify_company(db, sub.company_id, "Pagamento em atraso",
                             f"A cobrança de R$ {invoice.amount:.2f} venceu em {invoice.due_date}. Pague em até {billing.GRACE_DAYS} dias para não ter o acesso bloqueado.",
                             kind="WARNING")
    elif event in ("PAYMENT_DELETED", "PAYMENT_REFUNDED", "PAYMENT_CHARGEBACK_REQUESTED"):
        invoice.status = "CANCELED" if event == "PAYMENT_DELETED" else "REFUNDED"
    audit.record(db, f"WEBHOOK_{event}"[:50], company_id=sub.company_id, user_id=None, entity="invoice", entity_id=invoice.id,
                 details={"pagamento": p["id"], "valor": p.get("value")})
    await db.commit()
    return {"received": True}


# ---------- subscription, invoices, cancel ----------

@router.get("/subscription")
async def get_subscription(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    state = await billing.access_state(db, u)
    company = await db.get(CompanyModel, u["company_id"])
    return await _subscription_dict(db, state["subscription"], company, allowed=state["allowed"])


@router.get("/access")
async def get_access(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Lightweight check for the app shell (banner + redirect)."""
    state = await billing.access_state(db, u)
    sub = state["subscription"]
    return {"allowed": state["allowed"], "status": sub.status, "trial_ends_at": sub.trial_ends_at, "current_period_end": sub.current_period_end}


@router.get("/invoices")
async def get_invoices(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvoiceModel).join(SubscriptionModel, InvoiceModel.subscription_id == SubscriptionModel.id)
        .where(SubscriptionModel.company_id == u["company_id"]).order_by(InvoiceModel.created_at.desc())
    )
    return [_invoice_dict(i) for i in result.scalars().all()]


@router.post("/cancel")
async def cancel_subscription(u=Depends(get_current_user), db: AsyncSession = Depends(get_db),
                              provider: PaymentProvider | None = Depends(get_payment_provider)):
    """Stops renewals; access continues until the end of the period already paid."""
    _require_admin(u)
    subs = [s for s in await billing.live_subscriptions(db, u["company_id"]) if s.status in ("ACTIVE", "PAST_DUE", "PENDING")]
    if not subs:
        raise HTTPException(400, "Não há assinatura paga para cancelar")
    for sub in subs:
        if sub.provider_subscription_id and provider is not None and sub.provider == provider.name:
            try:
                await provider.cancel_subscription(sub.provider_subscription_id)
            except PaymentProviderError as e:
                raise HTTPException(502, str(e))
        sub.status = "CANCELED"
        sub.auto_renew = False
        sub.canceled_at = datetime.utcnow().isoformat()
    audit.record_by(db, u, "ASSINATURA_CANCELADA", entity="subscription", entity_id=subs[0].id)
    await db.commit()
    return {"message": "Assinatura cancelada. O acesso continua até o fim do período já pago."}


@router.get("/usage")
async def get_usage(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Plan consumption (bank connections, AI questions this month). Open even while access is blocked."""
    from app.core.plans import bank_connections_used, current_plan
    from app.integrations.ai.service import usage as ai_usage

    plan = await current_plan(db, u)
    ai = await ai_usage(db, u)
    await db.commit()
    return {
        "plan_id": plan["id"], "plan_name": plan["name"],
        "bank_connections": {"used": await bank_connections_used(db, u), "limit": plan["limits"].get("bank_connections", 0)},
        "ai_queries": ai,
    }
