"""Kanban board contents and card deletion (KAN-1, DB-4)."""


async def test_board_groups_cards_and_comments_and_delete_removes_card(client, company_a):
    h = company_a["headers"]
    proj = (await client.post("/kanban/projects", headers=h, json={"name": "Site"})).json()
    cols = (await client.get(f"/kanban/projects/{proj['id']}/board", headers=h)).json()["columns"]
    c1 = (await client.post("/kanban/cards", headers=h, json={"title": "A", "column_id": cols[0]["id"]})).json()
    c2 = (await client.post("/kanban/cards", headers=h, json={"title": "B", "column_id": cols[1]["id"]})).json()
    await client.post(f"/kanban/cards/{c1['id']}/comments", headers=h, json={"content": "primeiro"})
    await client.post(f"/kanban/cards/{c1['id']}/comments", headers=h, json={"content": "segundo"})

    board = (await client.get(f"/kanban/projects/{proj['id']}/board", headers=h)).json()
    by_col = {c["id"]: c["cards"] for c in board["columns"]}
    assert [c["title"] for c in by_col[cols[0]["id"]]] == ["A"]
    assert [c["title"] for c in by_col[cols[1]["id"]]] == ["B"]
    assert [m["content"] for m in by_col[cols[0]["id"]][0]["comments"]] == ["primeiro", "segundo"]
    assert by_col[cols[2]["id"]] == []

    assert (await client.delete(f"/kanban/cards/{c1['id']}", headers=h)).status_code == 200
    board = (await client.get(f"/kanban/projects/{proj['id']}/board", headers=h)).json()
    assert all(card["id"] != c1["id"] for col in board["columns"] for card in col["cards"])
    assert any(card["id"] == c2["id"] for col in board["columns"] for card in col["cards"])
