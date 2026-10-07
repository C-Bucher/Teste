from pathlib import Path

from app.core.legal import TERMS_VERSION


def test_frontend_and_backend_terms_versions_match():
    ts = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "legal.ts").read_text(encoding="utf-8")
    assert f"'{TERMS_VERSION}'" in ts, "bump frontend/src/legal.ts together with app/core/legal.py"
