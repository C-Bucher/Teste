# NOTA: Testa que toda chamada de API feita pelo frontend tem rota correspondente no backend (método e caminho).

"""Every API call the frontend makes must exist in the backend (method + path)."""

import re
from pathlib import Path

from app.main import app

FRONTEND = Path(__file__).resolve().parents[1] / "frontend" / "src"
CALL = re.compile(r"api\.(get|post|put|delete|patch)\(\s*([`'\"])(.*?)\2")


def _norm(path: str) -> str:
    path = re.sub(r"\$\{[^}]+\}", "{}", path).split("?")[0]
    return path.rstrip("/") or "/"


def test_frontend_calls_only_existing_routes():
    routes = set()
    for path, ops in app.openapi()["paths"].items():
        if path.startswith("/api/v1"):
            for method in ops:
                routes.add((method.upper(), _norm(re.sub(r"\{[^}]+\}", "{}", path[len("/api/v1"):]))))
    calls = set()
    for file in FRONTEND.rglob("*.ts*"):
        for m in CALL.finditer(file.read_text(encoding="utf-8")):
            calls.add((m.group(1).upper(), _norm(m.group(3)), file.name))
    assert len(calls) > 100, "the scan stopped finding calls; check the regex"
    missing = sorted(c for c in calls if (c[0], c[1]) not in routes)
    assert not missing, f"frontend calls with no backend route: {missing}"
