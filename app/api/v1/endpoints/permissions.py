import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.security import get_current_user
from app.core.permissions import MODULES, DEFAULT_PERMISSIONS
from app.db.session import get_db
from app.db.models import RolePermissionModel, CompanyModel

router = APIRouter()


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
async def put_matrix(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _require_admin(u)
    await db.execute(delete(RolePermissionModel).where(RolePermissionModel.company_id == u["company_id"]))
    for role in ("GERENTE", "FUNCIONARIO"):
        for module_key in d.get(role, []):
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
    await db.commit()
    return await get_matrix(u=u, db=db)


@router.get("/mine")
async def get_mine(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] == "ADMIN":
        return {"modules": MODULES}
    result = await db.execute(
        select(RolePermissionModel.module_key).where(
            RolePermissionModel.company_id == u["company_id"],
            RolePermissionModel.role == u["role"],
        )
    )
    modules = [row[0] for row in result.all()]
    company = await db.get(CompanyModel, u["company_id"])
    if not modules and u["role"] in DEFAULT_PERMISSIONS and not (company and company.permissions_customized):
        modules = DEFAULT_PERMISSIONS[u["role"]]
    return {"modules": modules}
