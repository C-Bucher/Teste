"""Company A's data must be invisible and untouchable for company B (MT-1), and personal data per user (MT-2)."""

from tests.conftest import register_admin


def _ids(payload):
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    return {x["id"] for x in items}


async def test_suppliers_are_isolated(client, company_a, company_b):
    r = await client.post("/suppliers/", headers=company_a["headers"], json={"name": "Fornecedor A", "company_id": company_b["user"]["company_id"]})
    sup = r.json()
    assert sup["company_id"] == company_a["user"]["company_id"], "company_id from the body must be ignored"

    assert sup["id"] not in _ids((await client.get("/suppliers/", headers=company_b["headers"])).json())
    assert (await client.get(f"/suppliers/{sup['id']}", headers=company_b["headers"])).status_code == 404
    assert (await client.put(f"/suppliers/{sup['id']}", headers=company_b["headers"], json={"name": "x"})).status_code == 404
    assert (await client.delete(f"/suppliers/{sup['id']}", headers=company_b["headers"])).status_code == 404
    assert (await client.get(f"/suppliers/{sup['id']}", headers=company_a["headers"])).json()["name"] == "Fornecedor A"


async def test_financial_entries_are_isolated(client, company_a, company_b):
    r = await client.post("/financial/entries", headers=company_a["headers"], json={"type": "RECEITA", "amount": 1234.5, "description": "Venda A", "due_date": "2026-10-10"})
    assert r.status_code == 200, r.text
    entry = r.json()

    assert entry["id"] not in _ids((await client.get("/financial/entries", headers=company_b["headers"])).json())
    for method, path, body in [
        ("get", f"/financial/entries/{entry['id']}", None),
        ("put", f"/financial/entries/{entry['id']}", {"amount": 1}),
        ("post", f"/financial/entries/{entry['id']}/pay", None),
    ]:
        kwargs = {"headers": company_b["headers"]}
        if body is not None:
            kwargs["json"] = body
        assert (await getattr(client, method)(path, **kwargs)).status_code == 404, path

    dre_b = (await client.get("/financial/dre", headers=company_b["headers"])).json()
    assert dre_b["total_receitas"] == 0


async def test_employees_are_isolated(client, company_a, company_b):
    emp = (await client.post("/employees/", headers=company_a["headers"], json={"full_name": "Colab A", "email": "colab.a@teste.com.br", "base_salary": 5000, "contract_type": "CLT", "role": "Dev"})).json()
    assert emp["id"] not in _ids((await client.get("/employees/", headers=company_b["headers"])).json())
    for method, path in [("get", f"/employees/{emp['id']}"), ("delete", f"/employees/{emp['id']}"),
                         ("post", f"/employees/{emp['id']}/terminate"), ("get", f"/employees/{emp['id']}/salary-history")]:
        assert (await getattr(client, method)(path, headers=company_b["headers"])).status_code == 404, path


async def test_clients_projects_and_cards_are_isolated(client, company_a, company_b):
    cli = (await client.post("/clients/", headers=company_a["headers"], json={"name": "Cliente A"})).json()
    assert cli["id"] not in _ids((await client.get("/clients/", headers=company_b["headers"])).json())
    assert (await client.put(f"/clients/{cli['id']}", headers=company_b["headers"], json={"name": "x"})).status_code == 404
    assert (await client.delete(f"/clients/{cli['id']}", headers=company_b["headers"])).status_code == 404

    # B cannot hang a project on A's client
    assert (await client.post("/kanban/projects", headers=company_b["headers"], json={"name": "P", "client_id": cli["id"]})).status_code == 404

    proj = (await client.post("/kanban/projects", headers=company_a["headers"], json={"name": "Projeto A", "client_id": cli["id"]})).json()
    assert proj["id"] not in _ids((await client.get("/kanban/projects", headers=company_b["headers"])).json())
    assert (await client.get(f"/kanban/projects/{proj['id']}/board", headers=company_b["headers"])).status_code == 404
    assert (await client.post(f"/kanban/projects/{proj['id']}/columns", headers=company_b["headers"], json={"name": "X"})).status_code == 404

    board = (await client.get(f"/kanban/projects/{proj['id']}/board", headers=company_a["headers"])).json()
    col_id = board["columns"][0]["id"]
    assert (await client.post("/kanban/cards", headers=company_b["headers"], json={"title": "intruso", "column_id": col_id})).status_code == 404

    card = (await client.post("/kanban/cards", headers=company_a["headers"], json={"title": "Card A", "column_id": col_id})).json()
    for method, path, body in [
        ("put", f"/kanban/cards/{card['id']}", {"title": "x"}),
        ("post", f"/kanban/cards/{card['id']}/move", {"column_id": col_id}),
        ("post", f"/kanban/cards/{card['id']}/comments", {"text": "x"}),
        ("post", f"/kanban/cards/{card['id']}/time/start", {}),
        ("delete", f"/kanban/cards/{card['id']}", None),
    ]:
        kwargs = {"headers": company_b["headers"]}
        if body is not None:
            kwargs["json"] = body
        assert (await getattr(client, method)(path, **kwargs)).status_code == 404, path

    # A card cannot be moved into another company's column
    proj_b = (await client.post("/kanban/projects", headers=company_b["headers"], json={"name": "Projeto B"})).json()
    col_b = (await client.get(f"/kanban/projects/{proj_b['id']}/board", headers=company_b["headers"])).json()["columns"][0]["id"]
    assert (await client.post(f"/kanban/cards/{card['id']}/move", headers=company_a["headers"], json={"column_id": col_b})).status_code == 404


async def test_exports_are_isolated(client, company_a, company_b):
    r = await client.post("/exports/request", headers=company_a["headers"], json={"type": "DRE", "format": "CSV"})
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    assert eid not in _ids((await client.get("/exports/logs", headers=company_b["headers"])).json())
    assert (await client.get(f"/exports/download/{eid}", headers=company_b["headers"])).status_code == 404


async def test_search_does_not_cross_companies(client, company_a, company_b):
    await client.post("/suppliers/", headers=company_a["headers"], json={"name": "Zebra Exclusiva LTDA"})
    r = await client.get("/search/", headers=company_b["headers"], params={"q": "Zebra Exclusiva"})
    assert r.status_code == 200
    assert "Zebra Exclusiva" not in r.text


async def test_personal_hub_is_isolated_per_user(client):
    alice = await register_admin(client, plan="plan-pessoal")
    bob = await register_admin(client, plan="plan-pessoal")

    created = {}
    for path, body in [
        ("/personal/accounts", {"name": "Conta Alice", "type": "CORRENTE", "balance": 900}),
        ("/personal/goals", {"name": "Viagem", "target_amount": 5000}),
        ("/personal/debts", {"name": "Carro", "total_amount": 30000, "installments_total": 48}),
        ("/personal/subscriptions", {"name": "Streaming", "amount": 39.9}),
        ("/personal/splits", {"description": "Jantar", "total_amount": 200}),
        ("/personal/budgets", {"category": "Lazer", "limit_amount": 400}),
        ("/personal/entries", {"type": "DESPESA", "amount": 50, "description": "Mercado", "category": "Alimentação"}),
    ]:
        r = await client.post(path, headers=alice["headers"], json=body)
        assert r.status_code == 200, (path, r.text)
        created[path] = r.json()["id"]

    for path, oid in created.items():
        listing = (await client.get(path, headers=bob["headers"])).json()
        assert oid not in _ids(listing), path
        assert (await client.delete(f"{path}/{oid}", headers=bob["headers"])).status_code == 404, path

    assert (await client.post(f"/personal/goals/{created['/personal/goals']}/contribute", headers=bob["headers"], json={"amount": 10})).status_code == 404


async def test_notifications_are_isolated(client, company_a, company_b):
    notes_a = (await client.get("/notifications/", headers=company_a["headers"])).json()
    notes_b = (await client.get("/notifications/", headers=company_b["headers"])).json()
    ids_a, ids_b = _ids(notes_a), _ids(notes_b)
    assert not (ids_a & ids_b)
    for nid in ids_a:
        assert (await client.post(f"/notifications/{nid}/read", headers=company_b["headers"])).status_code == 404


async def test_incomplete_payloads_are_400_not_500(client, company_a):
    r = await client.post("/employees/", headers=company_a["headers"], json={"full_name": "Sem Email"})
    assert r.status_code == 400
    r = await client.post("/suppliers/", headers=company_a["headers"], json={})
    assert r.status_code == 400
