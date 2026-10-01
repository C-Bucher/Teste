"""LGPD data-subject rights (export/delete own data) and admin access management (AUTH-2)."""

from tests.conftest import PASSWORD, create_member, register_admin


async def test_export_my_data(client):
    acc = await register_admin(client, plan="plan-completo")
    await client.post("/personal/accounts", headers=acc["headers"], json={"name": "Nubank", "balance": 10})
    r = await client.get("/account/export", headers=acc["headers"])
    assert r.status_code == 200
    data = r.json()
    assert data["perfil"]["email"] == acc["email"]
    assert "password_hash" not in data["perfil"]
    assert [x["name"] for x in data["dados_pessoais"]["personal_accounts"]] == ["Nubank"]
    assert any(e["action"] == "CADASTRO" for e in data["registro_de_atividades"])


async def test_delete_account_requires_password(client):
    acc = await register_admin(client)
    r = await client.request("DELETE", "/account", headers=acc["headers"], json={"password": "Errada123"})
    assert r.status_code == 400


async def test_last_admin_with_team_cannot_delete_account(client, company_a):
    await create_member(client, company_a, "FUNCIONARIO")
    r = await client.request("DELETE", "/account", headers=company_a["headers"], json={"password": PASSWORD})
    assert r.status_code == 400


async def test_member_deletes_own_account_and_personal_data(client, company_a):
    member = await create_member(client, company_a, "GERENTE")
    r = await client.request("DELETE", "/account", headers=member["headers"], json={"password": PASSWORD})
    assert r.status_code == 200, r.text
    assert (await client.post("/auth/login", json={"email": member["email"], "password": PASSWORD})).status_code == 401
    users = (await client.get("/auth/users", headers=company_a["headers"])).json()
    assert member["user"]["id"] not in {u["id"] for u in users}
    audit = (await client.get("/audit/", headers=company_a["headers"], params={"action": "CONTA_EXCLUIDA"})).json()
    assert audit["total"] == 1


async def test_sole_user_deletion_purges_the_company(client):
    acc = await register_admin(client)
    h = acc["headers"]
    sup = (await client.post("/suppliers/", headers=h, json={"name": "F"})).json()
    await client.post("/financial/entries", headers=h, json={"type": "DESPESA", "amount": 5, "supplier_id": sup["id"]})
    proj = (await client.post("/kanban/projects", headers=h, json={"name": "P"})).json()
    col = (await client.get(f"/kanban/projects/{proj['id']}/board", headers=h)).json()["columns"][0]["id"]
    card = (await client.post("/kanban/cards", headers=h, json={"title": "T", "column_id": col})).json()
    await client.post(f"/kanban/cards/{card['id']}/comments", headers=h, json={"content": "c"})
    await client.post("/employees/", headers=h, json={"full_name": "E", "email": "e@x.com", "base_salary": 1000, "contract_type": "PJ"})
    await client.post("/payments/checkout", headers=h, json={"plan_id": "plan-completo", "billing_cycle": "monthly", "payment_method": "pix"})
    await client.post("/personal/goals", headers=h, json={"name": "Meta", "target_amount": 100})

    r = await client.request("DELETE", "/account", headers=h, json={"password": PASSWORD})
    assert r.status_code == 200, r.text

    from sqlalchemy import select
    from app.db.models import Base, CompanyModel
    from app.db.session import async_session_maker
    company_id = acc["user"]["company_id"]
    async with async_session_maker() as s:
        assert await s.get(CompanyModel, company_id) is None
        for table in Base.metadata.sorted_tables:
            if "company_id" in table.c:
                left = (await s.execute(select(table).where(table.c.company_id == company_id))).all()
                assert left == [], table.name
            if "owner_id" in table.c:
                left = (await s.execute(select(table).where(table.c.owner_id == acc["user"]["id"]))).all()
                assert left == [], table.name


async def test_admin_changes_role_and_resets_password(client, company_a):
    member = await create_member(client, company_a, "FUNCIONARIO")
    r = await client.put(f"/auth/users/{member['user']['id']}", headers=company_a["headers"], json={"role": "GERENTE"})
    assert r.status_code == 200 and r.json()["role"] == "GERENTE"

    r = await client.post(f"/auth/users/{member['user']['id']}/reset-password", headers=company_a["headers"], json={"new_password": "Temporaria1"})
    assert r.status_code == 200, r.text
    assert (await client.get("/auth/me", headers=member["headers"])).status_code == 401, "old sessions must end"
    assert (await client.post("/auth/login", json={"email": member["email"], "password": "Temporaria1"})).status_code == 200


async def test_reset_password_is_admin_only_and_company_scoped(client, company_a, company_b):
    member_a = await create_member(client, company_a, "GERENTE")
    member_b = await create_member(client, company_b, "FUNCIONARIO")
    assert (await client.post(f"/auth/users/{member_b['user']['id']}/reset-password", headers=member_a["headers"], json={"new_password": "Temporaria1"})).status_code == 403
    assert (await client.post(f"/auth/users/{member_b['user']['id']}/reset-password", headers=company_a["headers"], json={"new_password": "Temporaria1"})).status_code == 404
    assert (await client.post(f"/auth/users/{member_a['user']['id']}/reset-password", headers=company_a["headers"], json={"new_password": "fraca"})).status_code == 400


async def test_other_admin_can_delete_account_when_another_admin_remains(client):
    acc = await register_admin(client)
    second = await create_member(client, acc, "FUNCIONARIO")
    await client.put(f"/auth/users/{second['user']['id']}", headers=acc["headers"], json={"role": "ADMIN"})
    r = await client.request("DELETE", "/account", headers=acc["headers"], json={"password": PASSWORD})
    assert r.status_code == 200, r.text
