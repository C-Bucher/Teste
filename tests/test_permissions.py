"""Module gates (SEC-1/SEC-3) and access-management rules (AUTH-2)."""

from tests.conftest import create_member, register_admin


async def test_funcionario_is_blocked_from_ungranted_modules(client, company_a):
    func = await create_member(client, company_a, "FUNCIONARIO")
    for path in ["/employees/", "/suppliers/", "/financial/entries", "/exports/logs", "/auth/users"]:
        assert (await client.get(path, headers=func["headers"])).status_code == 403, path
    assert (await client.get("/kanban/projects", headers=func["headers"])).status_code == 200


async def test_revoked_module_takes_effect_immediately(client, company_a):
    gerente = await create_member(client, company_a, "GERENTE")
    assert (await client.get("/suppliers/", headers=gerente["headers"])).status_code == 200

    r = await client.put("/permissions/matrix", headers=company_a["headers"], json={"GERENTE": ["dashboard", "kanban"], "FUNCIONARIO": ["dashboard"]})
    assert r.status_code == 200, r.text
    assert (await client.get("/suppliers/", headers=gerente["headers"])).status_code == 403
    assert (await client.get("/kanban/projects", headers=gerente["headers"])).status_code == 200

    r = await client.put("/permissions/matrix", headers=company_a["headers"], json={"GERENTE": ["dashboard", "kanban", "fornecedores"], "FUNCIONARIO": ["dashboard"]})
    assert (await client.get("/suppliers/", headers=gerente["headers"])).status_code == 200


async def test_personal_plan_cannot_reach_business_modules(client):
    pessoal = await register_admin(client, plan="plan-pessoal")
    assert (await client.get("/suppliers/", headers=pessoal["headers"])).status_code == 403


async def test_business_plan_cannot_reach_personal_hub(client):
    emp = await register_admin(client, plan="plan-empresarial")
    assert (await client.get("/personal/accounts", headers=emp["headers"])).status_code == 403


async def test_member_cannot_escalate_to_admin(client, company_a):
    func = await create_member(client, company_a, "FUNCIONARIO")
    r = await client.put(f"/auth/users/{func['user']['id']}", headers=func["headers"], json={"role": "ADMIN"})
    assert r.status_code == 403


async def test_admin_cannot_edit_users_of_another_company(client, company_a, company_b):
    func_b = await create_member(client, company_b, "FUNCIONARIO")
    r = await client.put(f"/auth/users/{func_b['user']['id']}", headers=company_a["headers"], json={"is_active": False})
    assert r.status_code == 404


async def test_last_admin_cannot_demote_itself(client, company_a):
    r = await client.put(f"/auth/users/{company_a['user']['id']}", headers=company_a["headers"], json={"role": "GERENTE"})
    assert r.status_code == 400
