"""SEC-4: password policy, password change, login lockout and access/refresh token separation."""

import uuid

import pytest

from tests.conftest import PASSWORD, register_admin


def _new_email():
    return f"u-{uuid.uuid4().hex[:8]}@teste.com.br"


@pytest.mark.parametrize("weak", ["curta1", "semnumeros", "12345678"])
async def test_register_rejects_weak_password(client, weak):
    r = await client.post("/auth/register", json={"full_name": "X", "email": _new_email(), "password": weak, "selected_plan": "plan-pessoal"})
    assert r.status_code == 400


async def test_create_user_rejects_weak_password(client, company_a):
    r = await client.post("/auth/users", headers=company_a["headers"], json={"full_name": "X", "email": _new_email(), "password": "12345678", "role": "FUNCIONARIO"})
    assert r.status_code == 400


async def test_change_password(client):
    acc = await register_admin(client)
    bad = await client.post("/auth/change-password", headers=acc["headers"], json={"current_password": "errada123", "new_password": "NovaSenha9"})
    assert bad.status_code == 400
    weak = await client.post("/auth/change-password", headers=acc["headers"], json={"current_password": PASSWORD, "new_password": "fraca"})
    assert weak.status_code == 400

    ok = await client.post("/auth/change-password", headers=acc["headers"], json={"current_password": PASSWORD, "new_password": "NovaSenha9"})
    assert ok.status_code == 200, ok.text
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).status_code == 401
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": "NovaSenha9"})).status_code == 200


def test_secret_key_has_no_public_default(monkeypatch):
    import importlib
    import app.core.config as config

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("APP_ENV", "development")
    try:
        reloaded = importlib.reload(config)
        assert reloaded.SECRET_KEY != "insecure-dev-secret-change-in-production"
        assert len(reloaded.SECRET_KEY) >= 32

        monkeypatch.setenv("APP_ENV", "production")
        with pytest.raises(RuntimeError):
            importlib.reload(config)
    finally:
        monkeypatch.undo()
        importlib.reload(config)


async def test_login_locks_after_five_failures(client):
    acc = await register_admin(client)
    for _ in range(5):
        assert (await client.post("/auth/login", json={"email": acc["email"], "password": "Errada123"})).status_code == 401
    locked = await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})
    assert locked.status_code == 429, "correct password must still be refused while locked"


async def test_successful_login_resets_failure_counter(client):
    acc = await register_admin(client)
    for _ in range(4):
        await client.post("/auth/login", json={"email": acc["email"], "password": "Errada123"})
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).status_code == 200
    for _ in range(4):
        await client.post("/auth/login", json={"email": acc["email"], "password": "Errada123"})
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).status_code == 200


async def test_lock_expires(client):
    acc = await register_admin(client)
    for _ in range(5):
        await client.post("/auth/login", json={"email": acc["email"], "password": "Errada123"})
    # simulate the 15 minutes passing by moving the lock into the past
    from app.db.session import async_session_maker
    from app.db.models import UserModel
    from sqlalchemy import update
    async with async_session_maker() as s:
        await s.execute(update(UserModel).where(UserModel.id == acc["user"]["id"]).values(locked_until="2000-01-01T00:00:00"))
        await s.commit()
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": PASSWORD})).status_code == 200


async def test_refresh_token_is_not_an_access_token(client):
    acc = await register_admin(client)
    tokens = acc["tokens"]
    assert tokens["refresh_token"] != tokens["access_token"]
    as_access = await client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert as_access.status_code == 401
    as_refresh = await client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert as_refresh.status_code == 401

    r = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    assert (await client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})).status_code == 200


async def test_password_change_revokes_old_tokens(client):
    acc = await register_admin(client)
    r = await client.post("/auth/change-password", headers=acc["headers"], json={"current_password": PASSWORD, "new_password": "NovaSenha9"})
    assert r.status_code == 200
    assert (await client.get("/auth/me", headers=acc["headers"])).status_code == 401
    assert (await client.post("/auth/refresh", json={"refresh_token": acc["tokens"]["refresh_token"]})).status_code == 401
    # the response of change-password carries fresh tokens so the current session continues
    fresh = r.json()["access_token"]
    assert (await client.get("/auth/me", headers={"Authorization": f"Bearer {fresh}"})).status_code == 200


async def test_deactivated_user_refresh_is_refused(client, company_a):
    from tests.conftest import create_member
    func = await create_member(client, company_a, "FUNCIONARIO")
    await client.put(f"/auth/users/{func['user']['id']}", headers=company_a["headers"], json={"is_active": False})
    assert (await client.post("/auth/refresh", json={"refresh_token": func["tokens"]["refresh_token"]})).status_code == 401
