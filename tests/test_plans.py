"""PLAN-1: the four commercial plans approved on 2026-09-30."""

from tests.conftest import register_admin

EXPECTED = {
    "plan-pessoal": ("pessoal", 29.90, 24.90),
    "plan-pessoal-conectado": ("pessoal", 59.90, 49.90),
    "plan-empresarial": ("empresarial", 249.00, 199.00),
    "plan-completo": ("completo", 299.00, 249.00),
}


async def test_catalog_has_the_four_approved_plans(client):
    plans = {p["id"]: p for p in (await client.get("/plans/")).json()}
    assert set(plans) == set(EXPECTED)
    for pid, (scope, monthly, yearly) in EXPECTED.items():
        assert plans[pid]["scope"] == scope
        assert plans[pid]["price_monthly"] == monthly
        assert plans[pid]["price_yearly"] == yearly
        assert "bank_connections" in plans[pid]["limits"]


async def test_catalog_promises_only_export_formats_that_exist(client):
    from app.api.v1.endpoints.exports import FORMATS
    text = (await client.get("/plans/")).text
    assert {"XLSX", "PDF", "CSV", "JSON"} <= set(FORMATS)
    assert "Excel, PDF, CSV e JSON" in text


async def test_checkout_charges_current_price_and_sets_scope(client):
    acc = await register_admin(client, plan="plan-pessoal")
    r = await client.post("/payments/checkout", headers=acc["headers"], json={
        "plan_id": "plan-pessoal-conectado", "billing_cycle": "monthly", "payment_method": "pix",
    })
    assert r.status_code == 200, r.text
    assert r.json()["subscription"]["amount"] == 59.90
    me = (await client.get("/auth/me", headers=acc["headers"])).json()
    assert me["plan_scope"] == "pessoal"


async def test_stored_plan_row_follows_catalog_price(client):
    """A PlanModel row saved with an old price must be refreshed on the next checkout."""
    from app.db.session import async_session_maker
    from app.db.models import PlanModel

    async with async_session_maker() as s:
        row = await s.get(PlanModel, "plan-empresarial")
        if row is None:
            s.add(PlanModel(id="plan-empresarial", name="Empresarial", price_monthly=1.0, price_yearly=1.0, max_employees=0, max_projects=0))
        else:
            row.price_monthly = 1.0
        await s.commit()

    acc = await register_admin(client, plan="plan-empresarial")
    r = await client.post("/payments/checkout", headers=acc["headers"], json={
        "plan_id": "plan-empresarial", "billing_cycle": "yearly", "payment_method": "pix",
    })
    assert r.status_code == 200, r.text
    assert r.json()["subscription"]["amount"] == 199.00 * 12
    async with async_session_maker() as s:
        assert (await s.get(PlanModel, "plan-empresarial")).price_monthly == 249.00
