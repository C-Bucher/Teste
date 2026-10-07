import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db, DATABASE_URL
from app.core.legal import TERMS_VERSION

router = APIRouter()


@router.get("/integrations")
async def get_integrations(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem ver o status das integrações")

    try:
        await db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        db_status = "offline"

    dialect = DATABASE_URL.split("://")[0].split("+")[0] if "://" in DATABASE_URL else "desconhecido"
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "integrations": [
            {"key": "database", "label": f"Banco de Dados ({dialect})", "status": db_status},
            {"key": "gemini", "label": "IA Gemini", "status": "configured" if gemini_configured else "unconfigured"},
        ]
    }



@router.get("/legal")
async def legal_info():
    """Public: the version of the terms of use and privacy policy currently in force."""
    return {"terms_version": TERMS_VERSION}
