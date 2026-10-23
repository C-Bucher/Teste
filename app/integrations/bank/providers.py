# NOTA: Interface para agregadores bancários (Open Finance). Só o Pluggy está implementado; sem credenciais, as rotas respondem 503.

"""Open Finance aggregators behind one interface, so the vendor can change without touching the rest.

Only Pluggy is implemented. It is enabled when PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET are set;
otherwise `get_bank_provider` returns None and the endpoints answer 503.
"""

import os
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import httpx

from app.integrations.bank.statement import ParsedTransaction


@dataclass
class ProviderAccount:
    id: str
    name: str
    bank_name: str | None = None


class BankProvider(Protocol):
    name: str

    async def create_connect_token(self, client_user_id: str) -> str: ...
    async def list_accounts(self, item_id: str) -> list[ProviderAccount]: ...
    async def list_transactions(self, account_id: str, since: date) -> list[ParsedTransaction]: ...


class ProviderError(RuntimeError):
    """The aggregator refused or failed; the message is safe to show."""


class PluggyProvider:
    """https://docs.pluggy.ai — API key from client credentials, then items/accounts/transactions."""

    name = "pluggy"
    BASE_URL = "https://api.pluggy.ai"

    def __init__(self, client_id: str, client_secret: str, base_url: str | None = None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url or self.BASE_URL

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=30) as http:
            auth = await http.post("/auth", json={"clientId": self._client_id, "clientSecret": self._client_secret})
            if auth.status_code != 200:
                raise ProviderError("Falha ao autenticar no agregador bancário")
            r = await http.request(method, path, headers={"X-API-KEY": auth.json()["apiKey"]}, **kwargs)
            if r.status_code >= 400:
                raise ProviderError(f"Agregador bancário respondeu {r.status_code}")
            return r.json()

    async def create_connect_token(self, client_user_id: str) -> str:
        data = await self._request("POST", "/connect_token", json={"clientUserId": client_user_id})
        return data["accessToken"]

    async def list_accounts(self, item_id: str) -> list[ProviderAccount]:
        item = await self._request("GET", f"/items/{item_id}")
        bank_name = (item.get("connector") or {}).get("name")
        data = await self._request("GET", "/accounts", params={"itemId": item_id})
        return [ProviderAccount(a["id"], a.get("name") or a.get("marketingName") or "Conta", bank_name) for a in data.get("results", [])]

    async def list_transactions(self, account_id: str, since: date) -> list[ParsedTransaction]:
        out: list[ParsedTransaction] = []
        page, total_pages = 1, 1
        while page <= total_pages:
            data = await self._request("GET", "/transactions", params={
                "accountId": account_id, "from": since.isoformat(), "pageSize": 500, "page": page,
            })
            total_pages = data.get("totalPages", 1)
            for t in data.get("results", []):
                amount = abs(float(t["amount"]))
                amount = -amount if t.get("type") == "DEBIT" else amount
                out.append(ParsedTransaction(t["id"], str(t["date"])[:10], round(amount, 2), t.get("description") or "(sem descrição)"))
            page += 1
        return out


def get_bank_provider() -> BankProvider | None:
    client_id, client_secret = os.getenv("PLUGGY_CLIENT_ID"), os.getenv("PLUGGY_CLIENT_SECRET")
    if client_id and client_secret:
        return PluggyProvider(client_id, client_secret)
    return None
