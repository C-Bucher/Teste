from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import EmployeeModel, ClientModel, ProjectModel, FinancialEntryModel, SupplierModel

router = APIRouter()

@router.get("/")
async def global_search(q: str = "", limit: int = 15, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = q.strip().lower()
    if len(q) < 2:
        return {"results": [], "total": 0, "query": q}

    results = []

    emp_result = await db.execute(select(EmployeeModel))
    for emp in emp_result.scalars().all():
        if q in (emp.full_name or "").lower() or q in (emp.role or "").lower() or q in (emp.email or "").lower():
            results.append({"type": "employee", "id": emp.id, "title": emp.full_name, "subtitle": emp.role or "", "url": "/employees"})

    cli_result = await db.execute(select(ClientModel))
    for cli in cli_result.scalars().all():
        if q in (cli.name or "").lower() or q in (cli.contact_name or "").lower() or q in (cli.segment or "").lower():
            results.append({"type": "client", "id": cli.id, "title": cli.name, "subtitle": cli.segment or "", "url": "/clients"})

    proj_result = await db.execute(select(ProjectModel))
    for proj in proj_result.scalars().all():
        if q in (proj.name or "").lower() or q in (proj.description or "").lower():
            results.append({"type": "project", "id": proj.id, "title": proj.name, "subtitle": proj.status or "", "url": f"/kanban/{proj.id}"})

    fin_result = await db.execute(select(FinancialEntryModel))
    for en in fin_result.scalars().all():
        if q in (en.description or "").lower() or q in (en.category or "").lower():
            results.append({"type": "financial", "id": en.id, "title": en.description, "subtitle": f"{en.type} · R$ {en.amount:,.2f}", "url": "/financial"})

    sup_result = await db.execute(select(SupplierModel))
    for sup in sup_result.scalars().all():
        if q in (sup.name or "").lower() or q in (sup.category or "").lower():
            results.append({"type": "supplier", "id": sup.id, "title": sup.name, "subtitle": sup.category or "", "url": "/suppliers"})

    return {"results": results[:limit], "total": len(results), "query": q}
