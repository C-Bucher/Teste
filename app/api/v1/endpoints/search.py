from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core.permissions import get_allowed_modules
from app.db.session import get_db
from app.db.models import EmployeeModel, ClientModel, ProjectModel, FinancialEntryModel, SupplierModel

router = APIRouter()

@router.get("")
@router.get("/")
async def global_search(q: str = "", limit: int = 15, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = q.strip().lower()
    if len(q) < 2:
        return {"results": [], "total": 0, "query": q}

    results = []
    allowed = await get_allowed_modules(u, db)

    if "equipe" in allowed:
        emp_result = await db.execute(select(EmployeeModel).where(EmployeeModel.company_id == u["company_id"]))
        for emp in emp_result.scalars().all():
            if q in (emp.full_name or "").lower() or q in (emp.role or "").lower() or q in (emp.email or "").lower():
                results.append({"type": "employee", "id": emp.id, "title": emp.full_name, "subtitle": f"{emp.role or ''} · {emp.email or ''}", "url": "/equipe"})

    if "kanban" in allowed:
        cli_result = await db.execute(select(ClientModel).where(ClientModel.company_id == u["company_id"]))
        for cli in cli_result.scalars().all():
            if q in (cli.name or "").lower() or q in (cli.contact_name or "").lower() or q in (cli.segment or "").lower():
                results.append({"type": "client", "id": cli.id, "title": cli.name, "subtitle": f"Cliente · {cli.segment or ''}", "url": "/kanban"})

    if "kanban" in allowed:
        proj_result = await db.execute(select(ProjectModel).where(ProjectModel.company_id == u["company_id"]))
        for proj in proj_result.scalars().all():
            if q in (proj.name or "").lower() or q in (proj.description or "").lower():
                results.append({"type": "project", "id": proj.id, "title": proj.name, "subtitle": f"Projeto · {proj.status or ''}", "url": f"/kanban?project={proj.id}"})

    if "financeiro" in allowed:
        fin_result = await db.execute(select(FinancialEntryModel).where(FinancialEntryModel.company_id == u["company_id"]))
        for en in fin_result.scalars().all():
            if q in (en.description or "").lower() or q in (en.category or "").lower():
                results.append({"type": "financial", "id": en.id, "title": en.description, "subtitle": f"Lançamento · {en.type} · R$ {en.amount:,.2f}", "url": "/financeiro"})

    if "fornecedores" in allowed:
        sup_result = await db.execute(select(SupplierModel).where(SupplierModel.company_id == u["company_id"]))
        for sup in sup_result.scalars().all():
            if q in (sup.name or "").lower() or q in (sup.category or "").lower():
                results.append({"type": "supplier", "id": sup.id, "title": sup.name, "subtitle": f"Fornecedor · {sup.category or ''}", "url": "/fornecedores"})

    return {"results": results[:limit], "total": len(results), "query": q}
