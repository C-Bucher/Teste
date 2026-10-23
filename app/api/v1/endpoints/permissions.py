# NOTA: Rotas /permissions: matriz de permissões por cargo (ler e salvar) e os módulos liberados para o usuário atual.

import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.security import get_current_user
from app.core import audit
from app.core.permissions import MODULES, DEFAULT_PERMISSIONS, get_allowed_modules
from app.db.session import get_db
from app.db.models import RolePermissionModel, CompanyModel

router = APIRouter()


class PermissionMatrixReq(BaseModel):
    GERENTE: list[str] = []
    FUNCIONARIO: list[str] = []


def _require_admin(u):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem gerenciar permissões")


@router.get("/matrix")
async def get_matrix(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(u)
    result = await db.execute(
        select(RolePermissionModel).where(RolePermissionModel.company_id == u["company_id"])
    )
    rows = result.scalars().all()
    company = await db.get(CompanyModel, u["company_id"])
    if not (company and company.permissions_customized):
        return {k: list(v) for k, v in DEFAULT_PERMISSIONS.items()}
    matrix: dict[str, list[str]] = {"GERENTE": [], "FUNCIONARIO": []}
    for r in rows:
        matrix.setdefault(r.role, []).append(r.module_key)
    return matrix


@router.put("/matrix")
async def put_matrix(d: PermissionMatrixReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(u)
    await db.execute(delete(RolePermissionModel).where(RolePermissionModel.company_id == u["company_id"]))
    for role in ("GERENTE", "FUNCIONARIO"):
        for module_key in getattr(d, role):
            if module_key not in MODULES:
                continue
            db.add(RolePermissionModel(
                id=f"rp-{uuid.uuid4().hex[:8]}",
                company_id=u["company_id"],
                role=role,
                module_key=module_key,
            ))
    company = await db.get(CompanyModel, u["company_id"])
    if company:
        company.permissions_customized = True
    audit.record_by(db, u, "PERMISSOES_ALTERADAS", entity="role_permissions", details={"GERENTE": d.GERENTE, "FUNCIONARIO": d.FUNCIONARIO})
    await db.commit()
    return await get_matrix(u=u, db=db)


@router.get("/mine")
async def get_mine(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return {"modules": await get_allowed_modules(u, db)}
