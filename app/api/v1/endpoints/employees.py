# NOTA: Rotas /employees: colaboradores (listar, criar, editar, excluir, desligar) e histórico de salário.
#       Calcula o CTC e o custo por hora de cada um.

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import date
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core import ctc as ctc_rules
from app.db.session import get_db
from app.db.models import EmployeeModel, SalaryHistoryModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_EMP_COLUMNS = {c.name for c in EmployeeModel.__table__.columns}


async def _compute_ctc(db: AsyncSession, company_id: str, base_salary: float, contract_type: Optional[str]):
    return ctc_rules.compute(base_salary, contract_type, await ctc_rules.get_params(db, company_id))


async def _add_salary_history(db: AsyncSession, employee: EmployeeModel, reason: str):
    db.add(SalaryHistoryModel(
        id=f"sh-{uuid.uuid4().hex[:8]}",
        employee_id=employee.id,
        base_salary=employee.base_salary,
        ctc_monthly=employee.ctc_monthly,
        ctc_snapshot=employee.ctc_snapshot,
        changed_at=date.today().isoformat(),
        reason=reason,
    ))


@router.get("/")
async def get_emps(skip: int = 0, limit: int = 100, active: Optional[bool] = None, search: Optional[str] = None, contract_type: Optional[str] = None, department: Optional[str] = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmployeeModel).where(EmployeeModel.company_id == u["company_id"]))
    e = models_to_dicts(result.scalars().all())
    e = [x for x in e if active is None or x["is_active"] == active]
    if search:
        s = search.lower()
        e = [x for x in e if s in (x.get("full_name") or "").lower() or s in (x.get("role") or "").lower() or s in (x.get("email") or "").lower() or s in (x.get("position") or "").lower()]
    if contract_type:
        e = [x for x in e if x.get("contract_type") == contract_type]
    if department:
        e = [x for x in e if department.lower() in (x.get("role") or "").lower()]
    return e[skip:skip + limit]


@router.post("/")
async def create_emp(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not str(d.get("full_name") or "").strip() or not str(d.get("email") or "").strip():
        raise HTTPException(400, "Nome e e-mail do colaborador são obrigatórios")
    ctc, hr = await _compute_ctc(db, u["company_id"], float(d.get("base_salary") or 0), d.get("contract_type"))
    emp_dict = {**d, "id": f"emp-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"], "ctc_snapshot": round(ctc, 2), "ctc_monthly": round(ctc, 2), "hourly_rate": hr, "hourly_cost": hr, "is_active": True, "position": d.get("role", ""), "hire_date": d.get("start_date", date.today().isoformat())}
    model_kwargs = {k: v for k, v in emp_dict.items() if k in _EMP_COLUMNS}
    emp = EmployeeModel(**model_kwargs)
    db.add(emp)
    await db.flush()
    await _add_salary_history(db, emp, "Cadastro inicial")
    await db.commit()
    await db.refresh(emp)
    return model_to_dict(emp)


@router.get("/{eid}")
async def get_emp(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(EmployeeModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    return model_to_dict(e)


@router.put("/{eid}")
async def upd_emp(eid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(EmployeeModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)

    old_base = e.base_salary
    old_contract = e.contract_type

    for k, v in d.items():
        if k in _EMP_COLUMNS and k not in {"id", "company_id"}:
            setattr(e, k, v)

    new_base = e.base_salary
    new_contract = e.contract_type
    salary_affecting = ("base_salary" in d and new_base != old_base) or ("contract_type" in d and new_contract != old_contract)

    if salary_affecting:
        ctc, hr = await _compute_ctc(db, u["company_id"], new_base or 0, new_contract)
        e.ctc_snapshot = ctc
        e.ctc_monthly = ctc
        e.hourly_rate = hr
        e.hourly_cost = hr
        await _add_salary_history(db, e, "Atualização de dados")

    await db.commit()
    await db.refresh(e)
    return model_to_dict(e)


@router.delete("/{eid}")
async def del_emp(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(EmployeeModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    e.is_active = False
    e.end_date = date.today().isoformat()
    await db.commit()
    return {"success": True}


@router.post("/{eid}/terminate")
async def term_emp(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(EmployeeModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    e.is_active = False
    e.end_date = date.today().isoformat()
    await db.commit()
    await db.refresh(e)
    return model_to_dict(e)


@router.get("/{eid}/salary-history")
async def sal_hist(eid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    e = await db.get(EmployeeModel, eid)
    if not e or e.company_id != u["company_id"]:
        raise HTTPException(404)
    result = await db.execute(select(SalaryHistoryModel).where(SalaryHistoryModel.employee_id == eid).order_by(SalaryHistoryModel.changed_at))
    return {"items": models_to_dicts(result.scalars().all())}
