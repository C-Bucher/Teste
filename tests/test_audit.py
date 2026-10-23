# NOTA: Testa a trilha de auditoria: ações sensíveis são registradas e só o administrador as vê.

"""SEC-2 (part 1): audit trail of sensitive actions, visible only to the company's admin."""

from tests.conftest import PASSWORD, create_member


async def _actions(client, admin, **params):
    r = await client.get("/audit/", headers=admin["headers"], params=params)
    assert r.status_code == 200, r.text
    return r.json()


async def test_sensitive_actions_are_audited(client, company_a):
    await client.post("/auth/login", json={"email": company_a["email"], "password": "Errada123"})
    await client.post("/auth/login", json={"email": company_a["email"], "password": PASSWORD})
    member = await create_member(client, company_a, "GERENTE")
    await client.put(f"/auth/users/{member['user']['id']}", headers=company_a["headers"], json={"role": "FUNCIONARIO"})
    await client.put("/permissions/matrix", headers=company_a["headers"], json={"GERENTE": ["dashboard"], "FUNCIONARIO": ["dashboard"]})
    entry = (await client.post("/financial/entries", headers=company_a["headers"], json={"type": "DESPESA", "amount": 99, "description": "Luz"})).json()
    await client.put(f"/financial/entries/{entry['id']}", headers=company_a["headers"], json={"amount": 120})
    await client.post(f"/financial/entries/{entry['id']}/pay", headers=company_a["headers"])

    page = await _actions(client, company_a, size=100)
    actions = [x["action"] for x in page["items"]]
    for expected in ["LOGIN_FALHA", "LOGIN", "USUARIO_CRIADO", "USUARIO_ALTERADO", "PERMISSOES_ALTERADAS",
                     "LANCAMENTO_CRIADO", "LANCAMENTO_ALTERADO", "LANCAMENTO_PAGO"]:
        assert expected in actions, expected
    changed = next(x for x in page["items"] if x["action"] == "LANCAMENTO_ALTERADO")
    assert changed["entity_id"] == entry["id"]
    assert changed["user_id"] == company_a["user"]["id"]
    assert "120" in changed["details"]


async def test_audit_is_admin_only_and_company_scoped(client, company_a, company_b):
    gerente = await create_member(client, company_a, "GERENTE")
    assert (await client.get("/audit/", headers=gerente["headers"])).status_code == 403

    await client.post("/suppliers/", headers=company_a["headers"], json={"name": "x"})
    await client.post("/auth/users", headers=company_a["headers"], json={"full_name": "Y", "email": "y-audit@teste.com.br", "password": PASSWORD, "role": "FUNCIONARIO"})
    items_b = (await _actions(client, company_b, size=100))["items"]
    assert all(x["company_id"] == company_b["user"]["company_id"] for x in items_b)
