# NOTA: Testa importação de extrato, conciliação, regras, isolamento entre empresas, limites do plano e o agregador.

"""Bank import, reconciliation, rules, isolation, plan limits and the aggregator provider (BANK-1, LIM-1)."""

from datetime import date, timedelta

import pytest

from app.integrations.bank.providers import ProviderAccount, get_bank_provider
from app.integrations.bank.statement import ParsedTransaction
from app.main import app
from tests.conftest import create_member, register_admin


def _d(days: int) -> date:
    return date.today() + timedelta(days=days)


def _csv(rows: list[tuple[date, str, str]]) -> bytes:
    lines = ["Data;Descrição;Valor"] + [f"{d.strftime('%d/%m/%Y')};{desc};{val}" for d, desc, val in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


async def _import(client, acc, content: bytes, scope="empresa", **extra):
    data = {"scope": scope, **extra}
    if "account_id" not in extra and "account_name" not in extra:
        data["account_name"] = "Conta Principal"
    return await client.post("/bank/import", headers=acc["headers"], data=data,
                             files={"file": ("extrato.csv", content, "text/csv")})


async def _entry(client, acc, **kw):
    body = {"type": "DESPESA", "amount": 100.0, "description": "x", "due_date": date.today().isoformat(), **kw}
    r = await client.post("/financial/entries", headers=acc["headers"], json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- import + reconciliation (empresa) ----------

async def test_import_reconciles_single_matching_payable_and_receivable(client, company_a):
    luz = await _entry(client, company_a, amount=320.50, description="Conta de luz", due_date=_d(-2).isoformat())
    venda = await _entry(client, company_a, type="RECEITA", amount=1500, description="Venda", due_date=_d(1).isoformat())
    await _entry(client, company_a, amount=999, description="Não pago ainda")

    r = await _import(client, company_a, _csv([(_d(0), "ENEL ENERGIA", "-320,50"), (_d(0), "PIX CLIENTE", "1.500,00"), (_d(0), "Tarifa", "-12,00")]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["imported"] == 3 and body["duplicates"] == 0 and body["reconciled"] == 2

    luz_after = (await client.get(f"/financial/entries/{luz['id']}", headers=company_a["headers"])).json()
    assert luz_after["status"] == "PAGO" and luz_after["payment_date"] == _d(0).isoformat()
    assert (await client.get(f"/financial/entries/{venda['id']}", headers=company_a["headers"])).json()["status"] == "PAGO"

    txs = (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa"})).json()
    by_desc = {t["description"]: t for t in txs}
    assert by_desc["ENEL ENERGIA"]["status"] == "CONCILIADA" and by_desc["ENEL ENERGIA"]["entry_id"] == luz["id"]
    assert by_desc["Tarifa"]["status"] == "NOVA"


async def test_reimporting_the_same_statement_does_not_duplicate(client, company_a):
    content = _csv([(_d(0), "Aluguel", "-2000,00")])
    first = (await _import(client, company_a, content)).json()
    again = (await _import(client, company_a, content, account_id=first["account"]["id"])).json()
    assert again["imported"] == 0 and again["duplicates"] == 1


async def test_ambiguous_match_is_left_for_the_user(client, company_a):
    await _entry(client, company_a, amount=50, description="A")
    await _entry(client, company_a, amount=50, description="B")
    body = (await _import(client, company_a, _csv([(_d(0), "Pagamento", "-50,00")]))).json()
    assert body["reconciled"] == 0


async def test_far_due_date_or_other_amount_does_not_match(client, company_a):
    await _entry(client, company_a, amount=80, due_date=_d(-20).isoformat())
    await _entry(client, company_a, amount=81)
    body = (await _import(client, company_a, _csv([(_d(0), "Pagamento", "-80,00")]))).json()
    assert body["reconciled"] == 0


async def test_manual_actions_create_entry_match_and_ignore(client, company_a):
    h = company_a["headers"]
    pending = await _entry(client, company_a, amount=70, due_date=_d(-30).isoformat())
    await _import(client, company_a, _csv([(_d(0), "Uber", "-35,00"), (_d(0), "Boleto antigo", "-70,00"), (_d(0), "Estorno", "5,00")]))
    txs = {t["description"]: t for t in (await client.get("/bank/transactions", headers=h, params={"scope": "empresa"})).json()}

    r = await client.post(f"/bank/transactions/{txs['Uber']['id']}/create-entry", headers=h, json={"category": "Transporte"})
    assert r.status_code == 200, r.text
    created = (await client.get(f"/financial/entries/{r.json()['entry_id']}", headers=h)).json()
    assert created["status"] == "PAGO" and created["type"] == "DESPESA" and created["amount"] == 35.0 and created["category"] == "Transporte"

    r = await client.post(f"/bank/transactions/{txs['Boleto antigo']['id']}/match", headers=h, json={"entry_id": pending["id"]})
    assert r.status_code == 200, r.text
    assert (await client.get(f"/financial/entries/{pending['id']}", headers=h)).json()["status"] == "PAGO"

    r = await client.post(f"/bank/transactions/{txs['Estorno']['id']}/ignore", headers=h)
    assert r.json()["status"] == "IGNORADA"
    # a transaction already handled cannot be handled again
    assert (await client.post(f"/bank/transactions/{txs['Uber']['id']}/ignore", headers=h)).status_code == 400


async def test_match_refuses_amount_mismatch(client, company_a):
    entry = await _entry(client, company_a, amount=10)
    await _import(client, company_a, _csv([(_d(0), "Algo", "-99,00")]))
    tx = (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa", "status": "NOVA"})).json()[0]
    assert (await client.post(f"/bank/transactions/{tx['id']}/match", headers=company_a["headers"], json={"entry_id": entry["id"]})).status_code == 400


async def test_rules_categorize_imported_transactions(client, company_a):
    h = company_a["headers"]
    assert (await client.post("/bank/rules", headers=h, json={"scope": "empresa", "pattern": "uber", "category": "Transporte"})).status_code == 200
    await _import(client, company_a, _csv([(_d(0), "UBER *TRIP", "-22,00")]))
    tx = (await client.get("/bank/transactions", headers=h, params={"scope": "empresa"})).json()[0]
    assert tx["category"] == "Transporte"


async def test_invalid_file_is_400(client, company_a):
    r = await client.post("/bank/import", headers=company_a["headers"], data={"scope": "empresa", "account_name": "X"},
                          files={"file": ("x.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 400


# ---------- personal ----------

async def test_personal_import_becomes_personal_entries(client):
    acc = await register_admin(client, plan="plan-pessoal")
    r = await _import(client, acc, _csv([(_d(0), "Mercado", "-150,00"), (_d(0), "Salário", "4.000,00")]), scope="pessoal")
    assert r.status_code == 200, r.text
    assert r.json()["launched"] == 2
    entries = (await client.get("/personal/entries", headers=acc["headers"])).json()["items"]
    got = sorted((e["type"], e["amount"]) for e in entries if e["description"] in ("Mercado", "Salário"))
    assert got == [("DESPESA", 150.0), ("RECEITA", 4000.0)]


# ---------- isolation ----------

async def test_bank_data_is_isolated_between_companies(client, company_a, company_b):
    body = (await _import(client, company_a, _csv([(_d(0), "Segredo A", "-1,00")]))).json()
    account_id = body["account"]["id"]
    assert (await client.get("/bank/accounts", headers=company_b["headers"], params={"scope": "empresa"})).json() == []
    assert (await client.get("/bank/transactions", headers=company_b["headers"], params={"scope": "empresa"})).json() == []
    assert (await _import(client, company_b, _csv([(_d(0), "x", "-1,00")]), account_id=account_id)).status_code == 404
    tx = (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa"})).json()[0]
    for path in [f"/bank/transactions/{tx['id']}/ignore", f"/bank/transactions/{tx['id']}/create-entry"]:
        assert (await client.post(path, headers=company_b["headers"], json={})).status_code == 404
    assert (await client.delete(f"/bank/accounts/{account_id}", headers=company_b["headers"])).status_code == 404
    # B cannot reconcile against A's entry either
    entry_a = await _entry(client, company_a, amount=1)
    await _import(client, company_b, _csv([(_d(0), "y", "-1,00")]))
    tx_b = (await client.get("/bank/transactions", headers=company_b["headers"], params={"scope": "empresa"})).json()[0]
    assert (await client.post(f"/bank/transactions/{tx_b['id']}/match", headers=company_b["headers"], json={"entry_id": entry_a["id"]})).status_code == 404


async def test_personal_bank_data_is_private_between_colleagues(client):
    owner = await register_admin(client, plan="plan-completo")
    colleague = await create_member(client, owner, "GERENTE")
    await _import(client, owner, _csv([(_d(0), "Particular", "-9,00")]), scope="pessoal")
    # colleague is in the same company but must not see the owner's personal bank data
    assert (await client.get("/bank/transactions", headers=colleague["headers"], params={"scope": "pessoal"})).json() == []


async def test_scope_requires_plan_and_module(client, company_a):
    pessoal = await register_admin(client, plan="plan-pessoal")
    assert (await _import(client, pessoal, _csv([(_d(0), "x", "-1,00")]), scope="empresa")).status_code == 403
    func = await create_member(client, company_a, "FUNCIONARIO")  # no financeiro module
    assert (await client.get("/bank/transactions", headers=func["headers"], params={"scope": "empresa"})).status_code == 403


# ---------- aggregator + limits ----------

class FakeProvider:
    name = "fake"

    def __init__(self):
        self.accounts = [ProviderAccount("pa-1", "Conta Corrente", "Banco Fake"), ProviderAccount("pa-2", "Poupança", "Banco Fake")]
        self.transactions = {"pa-1": [ParsedTransaction("t-1", date.today().isoformat(), -45.0, "Padaria")]}

    async def create_connect_token(self, client_user_id: str) -> str:
        return f"token-for-{client_user_id}"

    async def list_accounts(self, item_id: str):
        return self.accounts

    async def list_transactions(self, account_id: str, since: date):
        return self.transactions.get(account_id, [])


@pytest.fixture
def fake_provider():
    provider = FakeProvider()
    app.dependency_overrides[get_bank_provider] = lambda: provider
    yield provider
    app.dependency_overrides.pop(get_bank_provider, None)


async def test_aggregator_disabled_without_credentials(client, company_a):
    r = await client.post("/bank/connect-token", headers=company_a["headers"], json={"scope": "empresa"})
    assert r.status_code == 503


async def test_connect_sync_and_dedupe_via_aggregator(client, company_a, fake_provider):
    h = company_a["headers"]
    r = await client.post("/bank/connect-token", headers=h, json={"scope": "empresa"})
    assert r.status_code == 200 and r.json()["connect_token"].startswith("token-for-")
    r = await client.post("/bank/connections", headers=h, json={"scope": "empresa", "item_id": "item-1"})
    assert r.status_code == 200, r.text
    accounts = r.json()
    assert {a["name"] for a in accounts} == {"Conta Corrente", "Poupança"} and all(a["source"] == "agregador" for a in accounts)

    cc = next(a for a in accounts if a["provider_account_id"] == "pa-1")
    first = (await client.post(f"/bank/accounts/{cc['id']}/sync", headers=h)).json()
    assert first["imported"] == 1
    second = (await client.post(f"/bank/accounts/{cc['id']}/sync", headers=h)).json()
    assert second["imported"] == 0 and second["duplicates"] == 1


async def test_connection_limit_follows_the_plan(client, fake_provider):
    essencial = await register_admin(client, plan="plan-pessoal")
    r = await client.post("/bank/connect-token", headers=essencial["headers"], json={"scope": "pessoal"})
    assert r.status_code == 402  # Essencial has no bank connections: upgrade needed

    empresa = await register_admin(client, plan="plan-empresarial")  # 3 connections
    fake_provider.accounts = [ProviderAccount(f"pa-{i}", f"Conta {i}", "Banco") for i in range(4)]
    r = await client.post("/bank/connections", headers=empresa["headers"], json={"scope": "empresa", "item_id": "item-x"})
    assert r.status_code == 402
    fake_provider.accounts = fake_provider.accounts[:3]
    assert (await client.post("/bank/connections", headers=empresa["headers"], json={"scope": "empresa", "item_id": "item-x"})).status_code == 200

    usage = (await client.get("/bank/usage", headers=empresa["headers"])).json()
    assert usage["plan_id"] == "plan-empresarial" and usage["bank_connections"] == {"used": 3, "limit": 3}


async def test_deleting_account_removes_its_transactions(client, company_a):
    body = (await _import(client, company_a, _csv([(_d(0), "x", "-1,00")]))).json()
    assert (await client.delete(f"/bank/accounts/{body['account']['id']}", headers=company_a["headers"])).status_code == 200
    assert (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa"})).json() == []


async def test_ofx_reimport_without_choosing_account_reuses_the_same_account(client, company_a):
    from tests.test_statement_parser import OFX_SGML

    async def send():
        return await client.post("/bank/import", headers=company_a["headers"], data={"scope": "empresa", "account_name": "Qualquer"},
                                 files={"file": ("extrato.ofx", OFX_SGML, "application/x-ofx")})

    first = (await send()).json()
    second = (await send()).json()
    assert second["account"]["id"] == first["account"]["id"]
    assert second["imported"] == 0 and second["duplicates"] == 2
    assert len((await client.get("/bank/accounts", headers=company_a["headers"], params={"scope": "empresa"})).json()) == 1


# ---------- automatic sync: Pluggy webhook and scheduler endpoint ----------

async def _connected_account(client, acc, fake_provider, item_id):
    r = await client.post("/bank/connections", headers=acc["headers"], json={"scope": "empresa", "item_id": item_id})
    assert r.status_code == 200, r.text
    return next(a for a in r.json() if a["provider_account_id"] == "pa-1")


async def test_pluggy_webhook_syncs_the_item(client, company_a, fake_provider, monkeypatch):
    monkeypatch.setenv("PLUGGY_WEBHOOK_SECRET", "segredo-pluggy")
    await _connected_account(client, company_a, fake_provider, "item-webhook")
    bad = await client.post("/bank/webhook/pluggy", json={"event": "item/updated", "itemId": "item-webhook"}, headers={"x-webhook-secret": "x"})
    assert bad.status_code == 401
    ok = await client.post("/bank/webhook/pluggy", json={"event": "transactions/created", "itemId": "item-webhook"},
                           headers={"x-webhook-secret": "segredo-pluggy"})
    assert ok.status_code == 200 and ok.json()["synced_accounts"] >= 1
    txs = (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa"})).json()
    assert any(t["description"] == "Padaria" for t in txs)


async def test_scheduler_sync_all_needs_secret_and_skips_blocked_companies(client, fake_provider, monkeypatch):
    from datetime import datetime, timedelta as td
    from sqlalchemy import update
    from app.db.models import BankAccountModel, SubscriptionModel
    from app.db.session import async_session_maker

    monkeypatch.setenv("CRON_SECRET", "segredo-cron")
    active = await register_admin(client, plan="plan-empresarial")
    blocked = await register_admin(client, plan="plan-empresarial")
    a1 = await _connected_account(client, active, fake_provider, "item-a")
    a2 = await _connected_account(client, blocked, fake_provider, "item-b")
    async with async_session_maker() as s:
        await s.execute(update(SubscriptionModel).where(SubscriptionModel.company_id == blocked["user"]["company_id"])
                        .values(trial_ends_at=(datetime.utcnow() - td(days=1)).isoformat()))
        await s.commit()

    assert (await client.post("/bank/sync-all", headers={"x-cron-secret": "errado"})).status_code == 401
    r = await client.post("/bank/sync-all", headers={"x-cron-secret": "segredo-cron"})
    assert r.status_code == 200, r.text
    async with async_session_maker() as s:
        assert (await s.get(BankAccountModel, a1["id"])).last_sync_at is not None
        assert (await s.get(BankAccountModel, a2["id"])).last_sync_at is None
