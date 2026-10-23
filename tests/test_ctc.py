# NOTA: Testa que os parâmetros de CTC da empresa mudam o custo calculado do colaborador.

"""CFG-1: per-company CTC (custo total do colaborador) parameters drive the real calculation."""

from tests.conftest import create_member


async def test_defaults_match_previous_hardcoded_rule(client, company_a):
    params = (await client.get("/company/ctc-params", headers=company_a["headers"])).json()
    assert params["clt_multiplier"] == 1.75
    assert params["pj_multiplier"] == 1.10
    assert params["monthly_hours"] == 176
    emp = (await client.post("/employees/", headers=company_a["headers"], json={
        "full_name": "Ana", "email": "ana@x.com", "base_salary": 1000, "contract_type": "CLT", "role": "Dev"})).json()
    assert emp["ctc_monthly"] == 1750.0
    assert emp["hourly_cost"] == round(1750 / 176, 2)


async def test_saving_params_recalculates_active_employees(client, company_a):
    h = company_a["headers"]
    clt = (await client.post("/employees/", headers=h, json={"full_name": "C", "email": "c@x.com", "base_salary": 2000, "contract_type": "CLT", "role": "Dev"})).json()
    est = (await client.post("/employees/", headers=h, json={"full_name": "E", "email": "e@x.com", "base_salary": 1000, "contract_type": "ESTAGIO", "role": "Dev"})).json()

    r = await client.put("/company/ctc-params", headers=h, json={"clt_multiplier": 1.8, "pj_multiplier": 1.05, "estagio_multiplier": 1.2, "monthly_hours": 160})
    assert r.status_code == 200, r.text
    assert r.json()["recalculated_employees"] == 2

    clt_after = (await client.get(f"/employees/{clt['id']}", headers=h)).json()
    est_after = (await client.get(f"/employees/{est['id']}", headers=h)).json()
    assert clt_after["ctc_monthly"] == 3600.0
    assert clt_after["hourly_cost"] == round(3600 / 160, 2)
    assert est_after["ctc_monthly"] == 1200.0
    history = (await client.get(f"/employees/{clt['id']}/salary-history", headers=h)).json()["items"]
    assert any("CTC" in (x.get("reason") or "") for x in history)

    new = (await client.post("/employees/", headers=h, json={"full_name": "N", "email": "n@x.com", "base_salary": 1000, "contract_type": "PJ", "role": "Dev"})).json()
    assert new["ctc_monthly"] == 1050.0


async def test_params_are_per_company_and_validated(client, company_a, company_b):
    await client.put("/company/ctc-params", headers=company_a["headers"], json={"clt_multiplier": 2.0})
    assert (await client.get("/company/ctc-params", headers=company_b["headers"])).json()["clt_multiplier"] == 1.75
    assert (await client.put("/company/ctc-params", headers=company_a["headers"], json={"clt_multiplier": 0.5})).status_code == 400
    assert (await client.put("/company/ctc-params", headers=company_a["headers"], json={"monthly_hours": 0})).status_code == 400


async def test_only_configuracoes_module_can_edit(client, company_a):
    gerente = await create_member(client, company_a, "GERENTE")
    assert (await client.put("/company/ctc-params", headers=gerente["headers"], json={"clt_multiplier": 2})).status_code == 403
