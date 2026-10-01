"""IA-1 / LIM-1: model answers grounded on real data, honest rule-based fallback, history and quota."""

import json
from datetime import date, timedelta

import pytest

from app.integrations.ai.llm import LlmReply, LlmUnavailable, get_llm
from app.main import app
from tests.conftest import create_member, register_admin


class FakeLlm:
    model = "fake-model"

    def __init__(self, reply: str = "Resposta do modelo", fail: bool = False):
        self.reply, self.fail, self.calls = reply, fail, []

    async def generate(self, system, prompt, *, as_json=False):
        self.calls.append({"system": system, "prompt": prompt, "as_json": as_json})
        if self.fail:
            raise LlmUnavailable("simulada")
        return LlmReply(self.reply, self.model)


@pytest.fixture
def llm():
    fake = FakeLlm()
    app.dependency_overrides[get_llm] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_llm, None)


async def _pending(client, acc, kind, amount, days, desc):
    await client.post("/financial/entries", headers=acc["headers"], json={
        "type": kind, "amount": amount, "description": desc, "due_date": (date.today() + timedelta(days=days)).isoformat()})


# ---------- chat ----------

async def test_chat_uses_model_with_real_company_data_and_keeps_history(client, company_a, llm):
    await _pending(client, company_a, "DESPESA", 4321.0, 5, "Aluguel do galpão")
    r = await client.post("/ai/chat", headers=company_a["headers"], json={"message": "Como está meu caixa?"})
    assert r.status_code == 200, r.text
    assert r.json() == {"response": "Resposta do modelo", "source": "ia", "model": "fake-model"}
    prompt = llm.calls[0]["prompt"]
    assert "4321" in prompt and "Aluguel do galpão" in prompt and "Como está meu caixa?" in prompt

    await client.post("/ai/chat", headers=company_a["headers"], json={"message": "E no mês que vem?"})
    assert "Como está meu caixa?" in llm.calls[1]["prompt"], "recent conversation is sent as context"

    history = (await client.get("/ai/history", headers=company_a["headers"])).json()["items"]
    assert [m["role"] for m in history] == ["user", "assistant", "user", "assistant"]


async def test_chat_without_model_answers_with_real_numbers(client, company_a):
    await _pending(client, company_a, "DESPESA", 1000.0, 3, "Fornecedor X")
    await _pending(client, company_a, "RECEITA", 250.0, 4, "Cliente Y")
    r = (await client.post("/ai/chat", headers=company_a["headers"], json={"message": "como está o fluxo de caixa?"})).json()
    assert r["source"] == "regra"
    assert "R$ 250,00 a receber" in r["response"] and "R$ 1.000,00 a pagar" in r["response"]
    assert "48.000" not in r["response"], "no more hardcoded demo numbers"


async def test_model_failure_falls_back_to_rules(client, company_a, llm):
    llm.fail = True
    r = (await client.post("/ai/chat", headers=company_a["headers"], json={"message": "resultado do DRE"})).json()
    assert r["source"] == "regra" and "não respondeu" in r["response"]


async def test_history_is_private_to_each_user(client, company_a, llm):
    await client.post("/ai/chat", headers=company_a["headers"], json={"message": "pergunta do admin"})
    gerente = await create_member(client, company_a, "GERENTE")
    assert (await client.get("/ai/history", headers=gerente["headers"])).json()["items"] == []


# ---------- quota ----------

async def test_monthly_quota_follows_the_plan(client, llm, monkeypatch):
    from app.api.v1.endpoints import plans as plans_module
    acc = await register_admin(client, plan="plan-empresarial")
    patched = [dict(p, limits=dict(p["limits"], ai_queries=2)) if p["id"] == "plan-empresarial" else p for p in plans_module.PLANS_DB]
    monkeypatch.setattr("app.core.plans.PLANS_DB", patched)

    for _ in range(2):
        assert (await client.post("/ai/chat", headers=acc["headers"], json={"message": "oi"})).json()["source"] == "ia"
    third = (await client.post("/ai/chat", headers=acc["headers"], json={"message": "caixa"})).json()
    assert third["source"] == "regra" and "Limite mensal" in third["response"]
    assert len(llm.calls) == 2
    usage = (await client.get("/bank/usage", headers=acc["headers"])).json()
    assert usage["ai_queries"] == {"used": 2, "limit": 2}


# ---------- CFO insights ----------

async def test_cfo_insights_from_model(client, company_a, llm):
    llm.reply = json.dumps({"insights": [{"type": "ALERTA", "title": "Caixa", "description": "Falta R$ 10", "impact": "Alto", "urgency": "Alta"},
                                         {"type": "INVALIDO", "title": "x", "description": "y"}]})
    r = (await client.post("/ai/consultant/cfo", headers=company_a["headers"], json={})).json()
    assert r["source"] == "ia" and [i["title"] for i in r["insights"]] == ["Caixa"]
    assert llm.calls[0]["as_json"] is True


async def test_cfo_insights_fallback_reflects_real_situation(client, company_a):
    await _pending(client, company_a, "DESPESA", 500.0, -10, "Conta atrasada")
    r = (await client.post("/ai/consultant/cfo", headers=company_a["headers"], json={})).json()
    assert r["source"] == "regra"
    vencidas = next(i for i in r["insights"] if i["title"] == "Contas vencidas")
    assert "R$ 500,00" in vencidas["description"]


async def test_invalid_model_json_falls_back(client, company_a, llm):
    llm.reply = "isso não é json"
    r = (await client.post("/ai/consultant/cfo", headers=company_a["headers"], json={})).json()
    assert r["source"] == "regra" and r["insights"]


# ---------- categories for bank transactions ----------

async def _import(client, acc, rows):
    content = ("Data;Descrição;Valor\n" + "\n".join(f"{date.today().strftime('%d/%m/%Y')};{d};{v}" for d, v in rows) + "\n").encode()
    r = await client.post("/bank/import", headers=acc["headers"], data={"scope": "empresa", "account_name": "C"},
                          files={"file": ("e.csv", content, "text/csv")})
    assert r.status_code == 200, r.text


async def test_category_suggestions_with_and_without_model(client, company_a, llm):
    await _import(client, company_a, [("UBER *TRIP", "-30,00"), ("XPTO LTDA", "-99,00")])
    txs = {t["description"]: t["id"] for t in (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa"})).json()}

    llm.reply = json.dumps({"sugestoes": [{"id": txs["XPTO LTDA"], "categoria": "Serviços", "confianca": 0.8}]})
    res = {r["description"]: r for r in (await client.post("/ai/consultant/conciliation", headers=company_a["headers"], json={})).json()["results"]}
    assert res["XPTO LTDA"]["suggested_category"] == "Serviços" and res["XPTO LTDA"]["confidence"] == 0.8
    assert res["UBER *TRIP"]["suggested_category"] == "Transporte", "rules fill what the model skipped"

    r = await client.post(f"/bank/transactions/{txs['UBER *TRIP']}/category", headers=company_a["headers"], json={"category": "Transporte", "create_rule": True})
    assert r.status_code == 200 and r.json()["category"] == "Transporte"
    rules_ = (await client.get("/bank/rules", headers=company_a["headers"], params={"scope": "empresa"})).json()
    assert any(rule["category"] == "Transporte" for rule in rules_)


async def test_category_endpoint_is_isolated(client, company_a, company_b):
    await _import(client, company_a, [("Algo", "-1,00")])
    tx = (await client.get("/bank/transactions", headers=company_a["headers"], params={"scope": "empresa"})).json()[0]
    assert (await client.post(f"/bank/transactions/{tx['id']}/category", headers=company_b["headers"], json={"category": "X"})).status_code == 404
    assert (await client.post("/ai/consultant/conciliation", headers=company_b["headers"], json={})).json()["results"] == []


# ---------- proposal ----------

async def test_proposal_uses_model_hours_and_real_hourly_cost(client, company_a, llm):
    await client.post("/employees/", headers=company_a["headers"], json={"full_name": "Dev", "email": "d@x.com", "role": "Dev", "base_salary": 1760, "contract_type": "PJ"})
    llm.reply = json.dumps({"etapas": [{"nome": "Design", "horas": 10}, {"nome": "Código", "horas": 30}], "premissas": ["Sem integrações"]})
    r = await client.post("/ai/consultant/proposal", headers=company_a["headers"], json={"briefing": "Site institucional", "markup": 50})
    assert r.status_code == 200, r.text
    body = r.json()
    hourly = round(1760 * 1.10 / 176, 2)
    assert body["estimated_hours"] == 40 and body["hourly_cost"] == hourly
    assert body["estimated_internal_cost"] == round(40 * hourly, 2)
    assert body["suggested_price"] == round(body["estimated_internal_cost"] * 1.5, 2)
    assert body["margin_percentage"] == 33.3


async def test_proposal_without_model_or_team_is_refused_honestly(client, company_a):
    assert (await client.post("/ai/consultant/proposal", headers=company_a["headers"], json={"briefing": "x"})).status_code == 400  # no team yet
    await client.post("/employees/", headers=company_a["headers"], json={"full_name": "Dev", "email": "d2@x.com", "role": "Dev", "base_salary": 1000, "contract_type": "PJ"})
    assert (await client.post("/ai/consultant/proposal", headers=company_a["headers"], json={"briefing": "x"})).status_code == 503


# ---------- personal ----------

async def test_personal_insights_fallback_uses_real_subscriptions(client):
    acc = await register_admin(client, plan="plan-pessoal")
    await client.post("/personal/subscriptions", headers=acc["headers"], json={"name": "Streaming", "amount": 39.9})
    r = (await client.post("/personal/ai/insights", headers=acc["headers"], json={})).json()
    cut = next(i for i in r["insights"] if i["type"] == "CUT")
    assert cut["impact_value"] == 39.9 and "Streaming" in cut["message"]
    assert all("Lazer" not in i["message"] for i in r["insights"]), "no more hardcoded demo insight"


async def test_personal_insights_from_model(client, llm):
    acc = await register_admin(client, plan="plan-pessoal")
    llm.reply = json.dumps({"insights": [{"type": "CUT", "message": "Corte X", "impact_value": 12.5}]})
    r = (await client.post("/personal/ai/insights", headers=acc["headers"], json={})).json()
    assert r == {"insights": [{"type": "CUT", "message": "Corte X", "impact_value": 12.5}], "source": "ia"}
