# NOTA: Testa o login com 2FA (código e códigos de recuperação) e o limite de tentativas por IP.

"""AUTH-1 (TOTP two-factor login with recovery codes) and SEC-7 (per-IP rate limit on auth routes)."""

import pyotp

from tests.conftest import PASSWORD, create_member, register_admin


async def _enable_mfa(client, acc) -> tuple[pyotp.TOTP, list[str]]:
    setup = (await client.post("/auth/mfa/setup", headers=acc["headers"])).json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/") and setup["qr_svg"].startswith("data:image/svg+xml")
    totp = pyotp.TOTP(setup["secret"])
    assert (await client.post("/auth/mfa/enable", headers=acc["headers"], json={"code": "000000"})).status_code == 400
    r = await client.post("/auth/mfa/enable", headers=acc["headers"], json={"code": totp.now()})
    assert r.status_code == 200, r.text
    codes = r.json()["recovery_codes"]
    assert len(codes) == 8
    return totp, codes


async def test_login_requires_second_factor_once_enabled(client):
    acc = await register_admin(client)
    totp, _ = await _enable_mfa(client, acc)
    assert (await client.get("/auth/me", headers=acc["headers"])).json()["mfa_enabled"] is True

    step1 = (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).json()
    assert step1["mfa_required"] is True and "access_token" not in step1
    # the intermediate token is useless anywhere else
    assert (await client.get("/auth/me", headers={"Authorization": f"Bearer {step1['mfa_token']}"})).status_code == 401

    assert (await client.post("/auth/login/mfa", json={"mfa_token": step1["mfa_token"], "code": "123456"})).status_code == 401
    ok = await client.post("/auth/login/mfa", json={"mfa_token": step1["mfa_token"], "code": totp.now()})
    assert ok.status_code == 200 and "access_token" in ok.json()


async def test_recovery_code_works_once(client):
    acc = await register_admin(client)
    _, codes = await _enable_mfa(client, acc)
    step1 = (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).json()
    assert (await client.post("/auth/login/mfa", json={"mfa_token": step1["mfa_token"], "code": codes[0]})).status_code == 200
    step1 = (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).json()
    assert (await client.post("/auth/login/mfa", json={"mfa_token": step1["mfa_token"], "code": codes[0]})).status_code == 401


async def test_disable_requires_password_and_code(client):
    acc = await register_admin(client)
    totp, _ = await _enable_mfa(client, acc)
    assert (await client.post("/auth/mfa/disable", headers=acc["headers"], json={"password": "Errada123", "code": totp.now()})).status_code == 400
    assert (await client.post("/auth/mfa/disable", headers=acc["headers"], json={"password": PASSWORD, "code": "000000"})).status_code == 400
    assert (await client.post("/auth/mfa/disable", headers=acc["headers"], json={"password": PASSWORD, "code": totp.now()})).status_code == 200
    login = (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).json()
    assert "access_token" in login


async def test_admin_can_reset_a_members_second_factor(client, company_a):
    member = await create_member(client, company_a, "GERENTE")
    await _enable_mfa(client, member)
    other = await register_admin(client)
    assert (await client.post(f"/auth/users/{member['user']['id']}/mfa/disable", headers=other["headers"])).status_code == 404
    assert (await client.post(f"/auth/users/{member['user']['id']}/mfa/disable", headers=company_a["headers"])).status_code == 200
    login = (await client.post("/auth/login", json={"email": member["email"], "password": PASSWORD})).json()
    assert "access_token" in login


async def test_secret_is_not_stored_in_plain_text(client):
    acc = await register_admin(client)
    setup = (await client.post("/auth/mfa/setup", headers=acc["headers"])).json()
    from app.db.models import UserModel
    from app.db.session import async_session_maker
    async with async_session_maker() as s:
        stored = (await s.get(UserModel, acc["user"]["id"])).mfa_secret
    assert stored and setup["secret"] not in stored


async def test_auth_routes_are_rate_limited_per_ip(client, monkeypatch):
    from app.core import rate_limit
    monkeypatch.setattr(rate_limit, "LIMIT_PER_MINUTE", 3)
    monkeypatch.setattr(rate_limit, "TRUSTED_PROXY_HOPS", 1)  # behind one proxy: its X-Forwarded-For entry is trusted
    rate_limit.reset()
    for _ in range(3):
        assert (await client.post("/auth/forgot-password", json={"email": "x@y.com"})).status_code == 200
    blocked = await client.post("/auth/forgot-password", json={"email": "x@y.com"})
    assert blocked.status_code == 429 and blocked.headers.get("retry-after")
    # other IPs and non-auth routes are unaffected
    assert (await client.post("/auth/forgot-password", json={"email": "x@y.com"}, headers={"x-forwarded-for": "10.0.0.9"})).status_code == 200
    assert (await client.get("/plans/")).status_code == 200
    rate_limit.reset()


def test_forwarded_header_is_ignored_without_a_trusted_proxy():
    from types import SimpleNamespace
    from app.core import rate_limit
    req = SimpleNamespace(headers={"x-forwarded-for": "6.6.6.6"}, client=SimpleNamespace(host="127.0.0.1"))
    assert rate_limit.resolve_client_ip(req) == "127.0.0.1"
    req = SimpleNamespace(headers={"x-forwarded-for": "6.6.6.6, 200.1.1.1"}, client=SimpleNamespace(host="10.0.0.1"))
    rate_limit.TRUSTED_PROXY_HOPS = 1
    try:
        assert rate_limit.resolve_client_ip(req) == "200.1.1.1", "the entry added by our proxy, not the spoofable left one"
    finally:
        rate_limit.TRUSTED_PROXY_HOPS = 0
