from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid
from app.core.security import get_current_user

router = APIRouter()

# In-memory subscription storage
SUBSCRIPTIONS_DB = {
    "usr-001": {
        "id": "sub-001",
        "company_name": "TechConnect Soluções Ltda",
        "plan_id": "plan-pro",
        "plan_name": "Pro",
        "billing_cycle": "monthly",
        "amount": 249.00,
        "status": "ACTIVE",
        "payment_method": "credit_card",
        "card_last4": "4242",
        "card_brand": "Visa",
        "current_period_end": (datetime.now() + timedelta(days=30)).isoformat(),
        "auto_renew": True
    }
}

INVOICES_DB = [
    {
        "id": "inv-2026-001",
        "subscription_id": "sub-001",
        "amount": 249.00,
        "status": "PAID",
        "date": (datetime.now() - timedelta(days=5)).isoformat(),
        "pdf_url": "/api/v1/exports/invoice/inv-2026-001",
        "description": "Plano Pro - Mensalidade (Fevereiro 2026)"
    }
]

class CheckoutReq(BaseModel):
    plan_id: str
    billing_cycle: str  # 'monthly' or 'yearly'
    payment_method: str  # 'credit_card' or 'pix'
    card_number: Optional[str] = None
    card_name: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None
    company_name: Optional[str] = None
    cnpj_cpf: Optional[str] = None

@router.post("/checkout")
async def checkout(body: CheckoutReq, u=Depends(get_current_user)):
    plan_prices = {
        "plan-starter": {"monthly": 99.00, "yearly": 79.00 * 12, "name": "Starter"},
        "plan-pro": {"monthly": 249.00, "yearly": 199.00 * 12, "name": "Pro"},
        "plan-enterprise": {"monthly": 599.00, "yearly": 499.00 * 12, "name": "Enterprise"}
    }

    if body.plan_id not in plan_prices:
        raise HTTPException(status_code=400, detail="Plano inválido")

    price_info = plan_prices[body.plan_id]
    amount = price_info["monthly"] if body.billing_cycle == "monthly" else price_info["yearly"]

    sub_id = f"sub-{uuid.uuid4().hex[:6]}"
    inv_id = f"inv-{uuid.uuid4().hex[:6]}"
    
    last4 = body.card_number[-4:] if body.card_number and len(body.card_number) >= 4 else "8888"

    sub_data = {
        "id": sub_id,
        "company_name": body.company_name or "Sua Empresa",
        "plan_id": body.plan_id,
        "plan_name": price_info["name"],
        "billing_cycle": body.billing_cycle,
        "amount": amount,
        "status": "ACTIVE",
        "payment_method": body.payment_method,
        "card_last4": last4,
        "card_brand": "Visa",
        "current_period_end": (datetime.now() + timedelta(days=365 if body.billing_cycle == "yearly" else 30)).isoformat(),
        "auto_renew": True
    }
    SUBSCRIPTIONS_DB[u["id"]] = sub_data

    invoice_data = {
        "id": inv_id,
        "subscription_id": sub_id,
        "amount": amount,
        "status": "PAID",
        "date": datetime.now().isoformat(),
        "pdf_url": f"/api/v1/exports/invoice/{inv_id}",
        "description": f"Assinatura Plano {price_info['name']} ({'Anual' if body.billing_cycle == 'yearly' else 'Mensal'})"
    }
    INVOICES_DB.append(invoice_data)

    return {
        "success": True,
        "message": f"Pagamento realizado com sucesso! Seu plano {price_info['name']} está ativo.",
        "subscription": sub_data,
        "invoice": invoice_data,
        "pix_code": "00020126580014BR.GOV.BCB.PIX0136123e4567-e89b-12d3-a456-4266141740005204000053039865405" + str(int(amount)) + "5802BR5913TechConnect6009SAO PAULO62070503***6304E2CA" if body.payment_method == "pix" else None
    }

@router.get("/subscription")
async def get_subscription(u=Depends(get_current_user)):
    sub = SUBSCRIPTIONS_DB.get(u["id"])
    if not sub:
        # Default starter fallback
        sub = {
            "id": "sub-default",
            "company_name": "Sua Empresa",
            "plan_id": "plan-pro",
            "plan_name": "Pro",
            "billing_cycle": "monthly",
            "amount": 249.00,
            "status": "ACTIVE",
            "payment_method": "credit_card",
            "card_last4": "4242",
            "card_brand": "Mastercard",
            "current_period_end": (datetime.now() + timedelta(days=25)).isoformat(),
            "auto_renew": True
        }
    return sub

@router.get("/invoices")
async def get_invoices(u=Depends(get_current_user)):
    return INVOICES_DB
