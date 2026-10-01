"""Shared fixtures: a throwaway SQLite database and HTTP clients for two unrelated companies."""

import os
import tempfile
import uuid

import pytest

_DB_DIR = tempfile.mkdtemp(prefix="techconnect-tests-")
# TEST_DATABASE_URL runs the suite against a real server (e.g. a throwaway Postgres/MySQL container).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{_DB_DIR}/test.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-pytest-0123456789")
os.environ["APP_ENV"] = "test"
os.environ["STORAGE_DIR"] = os.path.join(_DB_DIR, "storage")

import httpx  # noqa: E402

from app.main import app  # noqa: E402
from app.db.session import init_db  # noqa: E402

PASSWORD = "Senha123"


@pytest.fixture(scope="session", autouse=True)
async def _database():
    await init_db()
    yield


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


async def register_admin(client: httpx.AsyncClient, plan: str = "plan-completo", company: str | None = None) -> dict:
    """Registers a brand-new company through the public endpoint and returns auth headers + user."""
    email = f"admin-{uuid.uuid4().hex[:8]}@teste.com.br"
    r = await client.post("/auth/register", json={
        "full_name": "Admin Teste",
        "email": email,
        "password": PASSWORD,
        "company_name": company or f"Empresa {uuid.uuid4().hex[:4]}",
        "selected_plan": plan,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    return {"headers": {"Authorization": f"Bearer {body['access_token']}"}, "user": body["user"], "email": email, "tokens": body}


async def create_member(client: httpx.AsyncClient, admin: dict, role: str) -> dict:
    email = f"{role.lower()}-{uuid.uuid4().hex[:8]}@teste.com.br"
    r = await client.post("/auth/users", headers=admin["headers"], json={
        "full_name": f"{role} Teste", "email": email, "password": PASSWORD, "role": role,
    })
    assert r.status_code == 200, r.text
    r = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    body = r.json()
    return {"headers": {"Authorization": f"Bearer {body['access_token']}"}, "user": body["user"], "email": email, "tokens": body}


@pytest.fixture
async def company_a(client):
    return await register_admin(client, company="Empresa A")


@pytest.fixture
async def company_b(client):
    return await register_admin(client, company="Empresa B")
