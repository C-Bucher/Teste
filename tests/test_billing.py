# NOTA: Testa teste grátis, checkout, webhook (ativação, renovação, atraso) e o bloqueio de acesso.

"""PAY-1: trial, real checkout through a payment provider, webhook-driven activation/renewal/overdue, access gate."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import update

from app.db.models import InvoiceModel, SubscriptionModel
from app.db.session import async_session_maker
from app.integrations.payments.providers import ProviderPayment, get_payment_provider
from app.main import app
from tests.conftest import register_admin

WEBHOOK_TOKEN = "token-webhook-teste"


class FakeAsaas:
    name = "asaas"

    def __init__(self):
        import uuid
        self.created, self.canceled, self.counter = [], [], 0
        self.run = uuid.uuid4().hex[:6]  # ids must be unique across tests sharing one database

    def sub(self, n):
        return f"sub_ext_{self.run}_{n}"

    def pay(self, n):
        return f"pay_{self.run}_{n}"

    async def ensure_customer(self, *, company_id, name, email, cpf_cnpj, existing_id=None):
        return existing_id or f"cus_{company_id}"

    async def create_subscription(self, *, customer_id, value, cycle, billing_type, description, external_reference):
        self.counter += 1
        sub_id = self.sub(self.counter)
        self.created.append({"customer": customer_id, "value": value, "cycle": cycle, "billing_type": billing_type, "ref": external_reference})
        payment = ProviderPayment(id=self.pay(self.counter), status="PENDING", value=value,
                                  due_date=date.today().isoformat(), invoice_url=f"https://pagar.example/{self.counter}")
        return sub_id, payment

    async def cancel_subscription(self, provider_subscription_id):
        self.canceled.append(provider_subscription_id)


@pytest.fixture
def asaas(monkeypatch):
    fake = FakeAsaas()
    app.dependency_overrides[get_payment_provider] = lambda: fake
    monkeypatch.setenv("ASAAS_WEBHOOK_TOKEN", WEBHOOK_TOKEN)
    yield fake
    app.dependency_overrides.pop(get_payment_provider, None)


async def _webhook(client, event, payment_id, sub_ext, **extra):
    body = {"event": event, "payment": {"id": payment_id, "subscription": sub_ext, "status": extra.pop("status", "CONFIRMED"),
                                        "value": extra.pop("value", 249.0), "dueDate": extra.pop("due", date.today().isoformat()),
                                        "invoiceUrl": "https://pagar.example/x", **extra}}
    return await client.post("/payments/webhook/asaas", json=body, headers={"asaas-access-token": WEBHOOK_TOKEN})


async def _sub_of(client, acc):
    return (await client.get("/payments/subscription", headers=acc["headers"])).json()


# ---------- trial and access gate ----------

async def test_new_company_starts_a_trial(client):
    acc = await register_admin(client, plan="plan-empresarial")
    sub = await _sub_of(client, acc)
    assert sub["status"] == "TRIAL" and sub["plan_id"] == "plan-empresarial"
    assert sub["access"]["allowed"] is True and sub["trial_ends_at"]
    assert (await client.get("/suppliers/", headers=acc["headers"])).status_code == 200


async def test_expired_trial_blocks_modules_but_not_billing_or_account(client):
    acc = await register_admin(client, plan="plan-completo")
    async with async_session_maker() as s:
        await s.execute(update(SubscriptionModel).where(SubscriptionModel.company_id == acc["user"]["company_id"])
                        .values(trial_ends_at=(datetime.utcnow() - timedelta(days=1)).isoformat()))
        await s.commit()
    blocked = await client.get("/suppliers/", headers=acc["headers"])
    assert blocked.status_code == 402 and blocked.headers.get("x-subscription") == "blocked"
    assert (await client.get("/personal/accounts", headers=acc["headers"])).status_code == 402
    for path in ["/payments/subscription", "/payments/invoices", "/auth/me", "/account/export", "/plans/"]:
        assert (await client.get(path, headers=acc["headers"])).status_code == 200, path
    assert (await _sub_of(client, acc))["access"]["allowed"] is False


# ---------- simulated provider (development only) ----------

async def test_simulated_checkout_activates_immediately_outside_production(client):
    acc = await register_admin(client, plan="plan-pessoal")
    r = await client.post("/payments/checkout", headers=acc["headers"], json={"plan_id": "plan-empresarial", "billing_cycle": "monthly", "payment_method": "pix"})
    assert r.status_code == 200, r.text
    assert r.json()["subscription"]["status"] == "ACTIVE" and r.json()["provider"] == "simulado"
    assert (await client.get("/auth/me", headers=acc["headers"])).json()["plan_scope"] == "empresarial"


async def test_simulated_provider_is_refused_in_production(client, monkeypatch):
    acc = await register_admin(client)
    monkeypatch.setenv("APP_ENV", "production")
    r = await client.post("/payments/checkout", headers=acc["headers"], json={"plan_id": "plan-empresarial", "billing_cycle": "monthly", "payment_method": "pix"})
    assert r.status_code == 503


# ---------- real provider flow ----------

async def test_checkout_creates_pending_payment_and_webhook_activates(client, asaas):
    acc = await register_admin(client, plan="plan-pessoal")
    bad = await client.post("/payments/checkout", headers=acc["headers"], json={"plan_id": "plan-empresarial", "billing_cycle": "yearly", "payment_method": "boleto", "cnpj_cpf": "123"})
    assert bad.status_code == 400, "CPF/CNPJ is required by the payment provider"
    r = await client.post("/payments/checkout", headers=acc["headers"], json={
        "plan_id": "plan-empresarial", "billing_cycle": "yearly", "payment_method": "boleto", "cnpj_cpf": "12.345.678/0001-95"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["subscription"]["status"] == "PENDING" and body["payment_url"].startswith("https://pagar.example/")
    assert asaas.created[0]["value"] == 199.0 * 12 and asaas.created[0]["cycle"] == "YEARLY" and asaas.created[0]["billing_type"] == "BOLETO"
    # still on the trial while the boleto is not paid
    assert (await client.get("/auth/me", headers=acc["headers"])).json()["plan_scope"] == "pessoal"

    assert (await client.post("/payments/webhook/asaas", json={"event": "PAYMENT_CONFIRMED", "payment": {"id": asaas.pay(1)}},
                              headers={"asaas-access-token": "errado"})).status_code == 401
    assert (await _webhook(client, "PAYMENT_CONFIRMED", asaas.pay(1), asaas.sub(1), value=2388.0)).status_code == 200
    assert (await _webhook(client, "PAYMENT_CONFIRMED", asaas.pay(1), asaas.sub(1), value=2388.0)).status_code == 200  # idempotent

    sub = await _sub_of(client, acc)
    assert sub["status"] == "ACTIVE" and sub["plan_id"] == "plan-empresarial"
    assert sub["current_period_end"][:10] >= (date.today() + timedelta(days=364)).isoformat()
    assert (await client.get("/auth/me", headers=acc["headers"])).json()["plan_scope"] == "empresarial"
    invoices = (await client.get("/payments/invoices", headers=acc["headers"])).json()
    assert [i["status"] for i in invoices].count("PAID") == 1


async def test_plan_change_replaces_and_cancels_previous_subscription(client, asaas):
    acc = await register_admin(client, plan="plan-empresarial")
    for plan in ("plan-empresarial", "plan-completo"):
        await client.post("/payments/checkout", headers=acc["headers"], json={"plan_id": plan, "billing_cycle": "monthly", "payment_method": "pix", "cnpj_cpf": "52998224725"})
    await _webhook(client, "PAYMENT_RECEIVED", asaas.pay(1), asaas.sub(1))
    await _webhook(client, "PAYMENT_RECEIVED", asaas.pay(2), asaas.sub(2), value=299.0)
    assert (await _sub_of(client, acc))["plan_id"] == "plan-completo"
    assert asaas.sub(1) in asaas.canceled


async def test_overdue_keeps_access_during_grace_then_blocks(client, asaas):
    acc = await register_admin(client, plan="plan-empresarial")
    await client.post("/payments/checkout", headers=acc["headers"], json={"plan_id": "plan-empresarial", "billing_cycle": "monthly", "payment_method": "pix", "cnpj_cpf": "52998224725"})
    await _webhook(client, "PAYMENT_CONFIRMED", asaas.pay(1), asaas.sub(1))
    # next cycle's charge is created, then becomes overdue
    await _webhook(client, "PAYMENT_CREATED", asaas.pay("r2"), asaas.sub(1), status="PENDING")
    await _webhook(client, "PAYMENT_OVERDUE", asaas.pay("r2"), asaas.sub(1), status="OVERDUE", due=(date.today() - timedelta(days=2)).isoformat())
    sub = await _sub_of(client, acc)
    assert sub["status"] == "PAST_DUE" and sub["access"]["allowed"] is True
    assert sub["pending_payment_url"]
    async with async_session_maker() as s:
        await s.execute(update(InvoiceModel).where(InvoiceModel.provider_payment_id == asaas.pay("r2")).values(due_date=(date.today() - timedelta(days=10)).isoformat()))
        await s.commit()
    assert (await client.get("/suppliers/", headers=acc["headers"])).status_code == 402
    # paying the overdue invoice restores access
    await _webhook(client, "PAYMENT_RECEIVED", asaas.pay("r2"), asaas.sub(1))
    assert (await client.get("/suppliers/", headers=acc["headers"])).status_code == 200


async def test_cancel_keeps_access_until_period_end(client, asaas):
    acc = await register_admin(client, plan="plan-empresarial")
    await client.post("/payments/checkout", headers=acc["headers"], json={"plan_id": "plan-empresarial", "billing_cycle": "monthly", "payment_method": "pix", "cnpj_cpf": "52998224725"})
    await _webhook(client, "PAYMENT_CONFIRMED", asaas.pay(1), asaas.sub(1))
    r = await client.post("/payments/cancel", headers=acc["headers"])
    assert r.status_code == 200
    assert asaas.sub(1) in asaas.canceled
    sub = await _sub_of(client, acc)
    assert sub["status"] == "CANCELED" and sub["access"]["allowed"] is True


async def test_only_admin_manages_billing(client, company_a, asaas):
    from tests.conftest import create_member
    gerente = await create_member(client, company_a, "GERENTE")
    assert (await client.post("/payments/checkout", headers=gerente["headers"], json={"plan_id": "plan-empresarial", "billing_cycle": "monthly", "payment_method": "pix", "cnpj_cpf": "52998224725"})).status_code == 403
    assert (await client.post("/payments/cancel", headers=gerente["headers"])).status_code == 403


async def test_unknown_webhook_payment_is_ignored(client, asaas):
    assert (await _webhook(client, "PAYMENT_CONFIRMED", "pay_desconhecido", "sub_inexistente")).status_code == 200


async def test_usage_is_available_even_when_blocked(client):
    acc = await register_admin(client, plan="plan-empresarial")
    async with async_session_maker() as s:
        await s.execute(update(SubscriptionModel).where(SubscriptionModel.company_id == acc["user"]["company_id"])
                        .values(trial_ends_at=(datetime.utcnow() - timedelta(days=1)).isoformat()))
        await s.commit()
    r = await client.get("/payments/usage", headers=acc["headers"])
    assert r.status_code == 200 and r.json()["ai_queries"]["limit"] == 3000
