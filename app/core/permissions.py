from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import RolePermissionModel, CompanyModel

MODULES = ["dashboard", "kanban", "equipe", "financeiro", "fornecedores", "configuracoes", "exportacao", "ia"]

DEFAULT_PERMISSIONS = {
    "GERENTE": ["dashboard", "kanban", "equipe", "financeiro", "fornecedores", "exportacao", "ia"],
    "FUNCIONARIO": ["dashboard", "kanban"],
}


async def get_allowed_modules(u: dict, db: AsyncSession) -> list[str]:
    if u["role"] == "ADMIN":
        return list(MODULES)
    result = await db.execute(
        select(RolePermissionModel.module_key).where(
            RolePermissionModel.company_id == u["company_id"],
            RolePermissionModel.role == u["role"],
        )
    )
    modules = [row[0] for row in result.all()]
    if modules:
        return modules
    company = await db.get(CompanyModel, u["company_id"]) if u["company_id"] else None
    if not (company and company.permissions_customized):
        return list(DEFAULT_PERMISSIONS.get(u["role"], []))
    return []


def require_module(module_key: str):
    async def _check(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if u.get("plan_scope") not in {"empresarial", "completo"}:
            raise HTTPException(403, "Seu plano não inclui os módulos empresariais")
        if u["role"] == "ADMIN":
            return u
        if module_key not in await get_allowed_modules(u, db):
            raise HTTPException(403, "Seu cargo não tem acesso a este módulo")
        return u
    return _check


def require_plan_scope(*allowed_scopes: str):
    async def _check(u=Depends(get_current_user)):
        if u.get("plan_scope") not in set(allowed_scopes):
            raise HTTPException(403, "Seu plano não inclui este módulo")
        return u
    return _check
