"""AUTH-3 (password recovery by e-mail) and NOT-1 (notification e-mails)."""

import re

import pytest

from app.core import mailer
from tests.conftest import PASSWORD, create_member, register_admin


@pytest.fixture(autouse=True)
def _clear_outbox():
    mailer.OUTBOX.clear()
    yield


def _token_from_last_mail(to: str) -> str:
    mail = next(m for m in reversed(mailer.OUTBOX) if m["to"] == to)
    return re.search(r"token=([A-Za-z0-9_\-]+)", mail["text"]).group(1)


async def test_forgot_and_reset_password(client):
    acc = await register_admin(client)
    r = await client.post("/auth/forgot-password", json={"email": acc["email"].upper()})
    assert r.status_code == 200
    token = _token_from_last_mail(acc["email"])

    assert (await client.post("/auth/reset-password", json={"token": token, "new_password": "fraca"})).status_code == 400
    r = await client.post("/auth/reset-password", json={"token": token, "new_password": "Recuperada1"})
    assert r.status_code == 200, r.text
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": "Recuperada1"})).status_code == 200
    assert (await client.get("/auth/me", headers=acc["headers"])).status_code == 401, "old sessions end"
    # single use
    assert (await client.post("/auth/reset-password", json={"token": token, "new_password": "OutraSenha2"})).status_code == 400
    assert any("senha foi alterada" in m["subject"].lower() for m in mailer.OUTBOX)


async def test_forgot_password_does_not_reveal_unknown_emails(client):
    r = await client.post("/auth/forgot-password", json={"email": "ninguem@teste.com.br"})
    assert r.status_code == 200
    assert list(mailer.OUTBOX) == []


async def test_reset_token_expires_and_new_request_invalidates_old(client):
    acc = await register_admin(client)
    await client.post("/auth/forgot-password", json={"email": acc["email"]})
    first = _token_from_last_mail(acc["email"])
    await client.post("/auth/forgot-password", json={"email": acc["email"]})
    second = _token_from_last_mail(acc["email"])
    assert (await client.post("/auth/reset-password", json={"token": first, "new_password": "Recuperada1"})).status_code == 400

    from sqlalchemy import update
    from app.db.models import PasswordResetModel
    from app.db.session import async_session_maker
    async with async_session_maker() as s:
        await s.execute(update(PasswordResetModel).values(expires_at="2000-01-01T00:00:00"))
        await s.commit()
    assert (await client.post("/auth/reset-password", json={"token": second, "new_password": "Recuperada1"})).status_code == 400


async def test_reset_unlocks_a_locked_account(client):
    acc = await register_admin(client)
    for _ in range(5):
        await client.post("/auth/login", json={"email": acc["email"], "password": "Errada123"})
    assert any("bloqueada" in m["subject"].lower() for m in mailer.OUTBOX), "lockout is notified by e-mail"
    await client.post("/auth/forgot-password", json={"email": acc["email"]})
    await client.post("/auth/reset-password", json={"token": _token_from_last_mail(acc["email"]), "new_password": "Recuperada1"})
    assert (await client.post("/auth/login", json={"email": acc["email"], "password": "Recuperada1"})).status_code == 200


async def test_welcome_and_access_emails(client):
    acc = await register_admin(client)
    assert any(m["to"] == acc["email"] and "bem-vindo" in m["subject"].lower() for m in mailer.OUTBOX)
    member = await create_member(client, acc, "GERENTE")
    mail = next(m for m in mailer.OUTBOX if m["to"] == member["email"])
    assert PASSWORD not in mail["text"], "never send passwords by e-mail"


async def test_bank_import_notifies_in_app_and_by_email_respecting_preferences(client, company_a):
    csv = "Data;Descrição;Valor\n01/10/2026;Algo;-1,00\n".encode()
    await client.post("/bank/import", headers=company_a["headers"], data={"scope": "empresa", "account_name": "C"},
                      files={"file": ("e.csv", csv, "text/csv")})
    notes = (await client.get("/notifications/", headers=company_a["headers"])).json()
    items = notes if isinstance(notes, list) else notes.get("items", [])
    assert any("Extrato importado" in n["title"] for n in items)
    assert any(m["to"] == company_a["email"] and "extrato" in m["subject"].lower() for m in mailer.OUTBOX)

    mailer.OUTBOX.clear()
    await client.put("/notifications/preferences", headers=company_a["headers"], json={"email_enabled": False})
    await client.post("/bank/import", headers=company_a["headers"], data={"scope": "empresa", "account_name": "D"},
                      files={"file": ("e.csv", csv, "text/csv")})
    assert not any(m["to"] == company_a["email"] for m in mailer.OUTBOX)
