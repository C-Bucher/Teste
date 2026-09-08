from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import RolePermissionModel

MODULES = ["dashboard", "kanban", "equipe", "financeiro", "fornecedores", "configuracoes", "exportacao", "ia"]

DEFAULT_PERMISSIONS = {
    "GERENTE": ["dashboard", "kanban", "equipe", "financeiro", "fornecedores", "exportacao", "ia"],
    "FUNCIONARIO": ["dashboard", "kanban"],
}


def require_module(module_key: str):
    async def _check(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if u["role"] == "ADMIN":
            return u
        result = await db.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.company_id == u["company_id"],
                RolePermissionModel.role == u["role"],
                RolePermissionModel.module_key == module_key,
            )
        )
        if not result.scalars().first():
            raise HTTPException(403, "Seu cargo não tem acesso a este módulo")
        return u
    return _check
