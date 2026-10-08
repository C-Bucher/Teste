"""SEC-2: acceptance of the terms of use and privacy policy, recorded with version and date."""

import uuid

from app.core.legal import TERMS_VERSION
from tests.conftest import create_member


async def test_register_requires_accepting_the_terms(client):
    body = {"full_name": "X", "email": f"t-{uuid.uuid4().hex[:6]}@teste.com.br", "password": "Senha123", "selected_plan": "plan-pessoal"}
    assert (await client.post("/auth/register", json={**body, "accept_terms": False})).status_code == 400
    assert (await client.post("/auth/register", json=body)).status_code == 400
    r = await client.post("/auth/register", json={**body, "accept_terms": True})
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["terms_version"] == TERMS_VERSION and user["terms_accepted_at"]


async def test_member_accepts_on_first_access(client, company_a):
    member = await create_member(client, company_a, "FUNCIONARIO")
    me = (await client.get("/auth/me", headers=member["headers"])).json()
    assert me["terms_version"] is None
    r = await client.post("/auth/accept-terms", headers=member["headers"], json={"version": TERMS_VERSION})
    assert r.status_code == 200
    assert (await client.get("/auth/me", headers=member["headers"])).json()["terms_version"] == TERMS_VERSION
    assert (await client.post("/auth/accept-terms", headers=member["headers"], json={"version": "1999-01-01"})).status_code == 400


async def test_terms_version_is_public(client):
    r = await client.get("/system/legal")
    assert r.status_code == 200 and r.json()["terms_version"] == TERMS_VERSION
