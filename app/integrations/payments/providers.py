# NOTA: Provedores de pagamento da assinatura: Asaas (real; o cartão é digitado na página do Asaas)
#       e um provedor simulado, que só existe fora de produção.

"""Payment providers for the subscription billing (PAY-1).

Asaas is the real one: it hosts the payment page (Pix, boleto, card), so card data never reaches
TechConnect. The simulated provider confirms instantly and exists only outside production.
"""

import os
from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass
class ProviderPayment:
    id: str
    status: str            # PENDING | CONFIRMED | RECEIVED | OVERDUE | ...
    value: float
    due_date: str          # ISO date
    invoice_url: str | None


class PaymentProviderError(RuntimeError):
    """The provider refused or failed; the message is safe to show."""


class PaymentProvider(Protocol):
    name: str

    async def ensure_customer(self, *, company_id: str, name: str, email: str, cpf_cnpj: str, existing_id: str | None = None) -> str: ...
    async def create_subscription(self, *, customer_id: str, value: float, cycle: str, billing_type: str,
                                  description: str, external_reference: str) -> tuple[str, ProviderPayment | None]: ...
    async def cancel_subscription(self, provider_subscription_id: str) -> None: ...


class SimulatedProvider:
    """Development only: every checkout is paid on the spot."""
    name = "simulado"

    async def ensure_customer(self, *, company_id, name, email, cpf_cnpj, existing_id=None) -> str:
        return existing_id or f"sim-cus-{company_id}"

    async def create_subscription(self, *, customer_id, value, cycle, billing_type, description, external_reference):
        return f"sim-sub-{external_reference}", None

    async def cancel_subscription(self, provider_subscription_id) -> None:
        return None


class AsaasProvider:
    """https://docs.asaas.com — customers, recurring subscriptions and their payments."""
    name = "asaas"

    def __init__(self, api_key: str, sandbox: bool):
        self._key = api_key
        self._base = "https://sandbox.asaas.com/api/v3" if sandbox else "https://api.asaas.com/v3"

    async def _call(self, method: str, path: str, **kwargs) -> dict:
        headers = {"access_token": self._key, "User-Agent": "TechConnect/2.0", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(base_url=self._base, timeout=30) as http:
                r = await http.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError:
            raise PaymentProviderError("Não foi possível falar com o Asaas agora. Tente novamente em instantes")
        if r.status_code >= 400:
            try:
                msg = "; ".join(e.get("description", "") for e in r.json().get("errors", [])) or f"erro {r.status_code}"
            except ValueError:
                msg = f"erro {r.status_code}"
            raise PaymentProviderError(f"Asaas recusou a operação: {msg}")
        return r.json() if r.content else {}

    async def ensure_customer(self, *, company_id, name, email, cpf_cnpj, existing_id=None) -> str:
        if existing_id:
            return existing_id
        data = await self._call("POST", "/customers", json={
            "name": name, "email": email, "cpfCnpj": cpf_cnpj, "externalReference": company_id, "notificationDisabled": False,
        })
        return data["id"]

    async def create_subscription(self, *, customer_id, value, cycle, billing_type, description, external_reference):
        from datetime import date
        sub = await self._call("POST", "/subscriptions", json={
            "customer": customer_id, "billingType": billing_type, "value": round(value, 2), "cycle": cycle,
            "nextDueDate": date.today().isoformat(), "description": description, "externalReference": external_reference,
        })
        payments = (await self._call("GET", f"/subscriptions/{sub['id']}/payments")).get("data", [])
        first = None
        if payments:
            p = payments[0]
            first = ProviderPayment(p["id"], p.get("status", "PENDING"), float(p.get("value", value)), p.get("dueDate"), p.get("invoiceUrl"))
        return sub["id"], first

    async def cancel_subscription(self, provider_subscription_id) -> None:
        await self._call("DELETE", f"/subscriptions/{provider_subscription_id}")


def get_payment_provider() -> PaymentProvider | None:
    key = os.getenv("ASAAS_API_KEY", "").strip()
    if key:
        return AsaasProvider(key, sandbox=os.getenv("ASAAS_ENV", "sandbox").lower() != "production")
    if os.getenv("APP_ENV", "development").lower() != "production":
        return SimulatedProvider()
    return None
