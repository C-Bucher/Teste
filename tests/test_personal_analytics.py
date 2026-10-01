"""Personal net-worth series comes from the person's real accounts, debts and entries."""

from datetime import date

from tests.conftest import register_admin


def _month_start(offset: int) -> date:
    today = date.today()
    y, m = today.year, today.month - offset
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


async def test_net_worth_series_is_derived_from_real_data(client):
    acc = await register_admin(client, plan="plan-pessoal")
    h = acc["headers"]
    await client.post("/personal/accounts", headers=h, json={"name": "Conta", "type": "CONTA", "balance": 5000})
    await client.post("/personal/accounts", headers=h, json={"name": "Cartão", "type": "CARTAO", "balance": -1000})
    await client.post("/personal/debts", headers=h, json={"name": "Carro", "total_amount": 3000, "remaining_amount": 2000})
    # income earned this month and last month: earlier months must have had less
    await client.post("/personal/entries", headers=h, json={"type": "RECEITA", "amount": 700, "date": date.today().isoformat(), "category": "Salário"})
    await client.post("/personal/entries", headers=h, json={"type": "DESPESA", "amount": 200, "date": _month_start(1).isoformat(), "category": "Mercado"})

    series = (await client.get("/personal/analytics", headers=h)).json()["net_worth_series"]
    assert len(series) == 6
    now = 5000 - 1000 - 2000
    assert series[-1]["value"] == now
    assert series[-2]["value"] == now - 700            # before this month's income
    assert series[-3]["value"] == now - 700 + 200      # before last month's expense
    assert series[0]["value"] == series[-3]["value"]


async def test_net_worth_is_flat_without_entries(client):
    acc = await register_admin(client, plan="plan-pessoal")
    series = (await client.get("/personal/analytics", headers=acc["headers"])).json()["net_worth_series"]
    assert [p["value"] for p in series] == [0] * 6
