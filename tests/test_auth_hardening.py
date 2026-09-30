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
