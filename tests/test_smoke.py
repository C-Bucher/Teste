# NOTA: Teste rápido: cadastro, login e /me funcionam, e sem token a API recusa.

async def test_register_login_and_me(client, company_a):
    r = await client.get("/auth/me", headers=company_a["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == company_a["email"]
    assert "password_hash" not in r.json()


async def test_requests_without_token_are_rejected(client):
    r = await client.get("/suppliers/")
    assert r.status_code == 401
