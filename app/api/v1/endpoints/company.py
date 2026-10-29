# NOTA: Rotas /company: dados da empresa, conclusão do onboarding, centros de custo, categorias (plano de contas),
#       calendário de trabalho e parâmetros do CTC.

from fastapi import APIRouter, HTTPException, Depends
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core.permissions import require_module
from app.db.session import get_db
from app.db.models import CompanyModel, CostCenterModel, CategoryModel, WorkCalendarModel, EmployeeModel, SalaryHistoryModel
from app.core import audit, ctc as ctc_rules
from datetime import date
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_COMPANY_COLUMNS = {c.name for c in CompanyModel.__table__.columns}
_CC_COLUMNS = {c.name for c in CostCenterModel.__table__.columns}
_CAT_COLUMNS = {c.name for c in CategoryModel.__table__.columns}


async def _get_company(db: AsyncSession, company_id: str | None) -> CompanyModel | None:
    return await db.get(CompanyModel, company_id) if company_id else None


@router.get("/")
async def get_company(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await _get_company(db, u["company_id"])
    if not company:
        raise HTTPException(404)
    return model_to_dict(company)


@router.put("/")
async def upd_company(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
    company = await _get_company(db, u["company_id"])
    if not company:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _COMPANY_COLUMNS and k not in {"id", "created_at", "onboarding_completed", "permissions_customized"}:
            setattr(company, k, v)
    await db.commit()
    await db.refresh(company)
    return model_to_dict(company)


@router.post("/onboarding/complete")
async def complete_onboarding(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem concluir a configuração inicial")
    company = await _get_company(db, u["company_id"])
    if not company:
        raise HTTPException(404)
    company.onboarding_completed = True
    await db.commit()
    await db.refresh(company)
    return model_to_dict(company)


@router.get("/cost-centers")
async def get_cc(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CostCenterModel).where(CostCenterModel.company_id == u["company_id"]))
    return models_to_dicts(result.scalars().all())


@router.post("/cost-centers")
async def create_cc(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
    cc_dict = {**d, "id": f"cc-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"]}
    model_kwargs = {k: v for k, v in cc_dict.items() if k in _CC_COLUMNS}
    cc = CostCenterModel(**model_kwargs)
    db.add(cc)
    await db.commit()
    await db.refresh(cc)
    return model_to_dict(cc)


@router.delete("/cost-centers/{cid}")
async def del_cc(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
    cc = await db.get(CostCenterModel, cid)
    if not cc or cc.company_id != u["company_id"]:
        raise HTTPException(404)
    await db.delete(cc)
    await db.commit()
    return {"success": True}


@router.get("/categories")
async def get_cats(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CategoryModel).where(CategoryModel.company_id == u["company_id"]))
    return models_to_dicts(result.scalars().all())


@router.post("/categories")
async def create_cat(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
    cat_dict = {**d, "id": f"cat-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"]}
    model_kwargs = {k: v for k, v in cat_dict.items() if k in _CAT_COLUMNS}
    c = CategoryModel(**model_kwargs)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return model_to_dict(c)


async def _calendar(db: AsyncSession, company_id: str) -> WorkCalendarModel:
    calendar = await db.get(WorkCalendarModel, company_id)
    if calendar is None:
        calendar = WorkCalendarModel(company_id=company_id)
        db.add(calendar)
        await db.commit()
        await db.refresh(calendar)
    return calendar

@router.get("/calendar")
async def get_calendar(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return model_to_dict(await _calendar(db, u["company_id"]))
@router.put("/calendar")
async def upd_calendar(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
    calendar = await _calendar(db, u["company_id"])
    for key in ("work_days", "work_hours_per_day", "holidays"):
        if key in d:
            setattr(calendar, key, d[key])
    await db.commit()
    await db.refresh(calendar)
    return model_to_dict(calendar)

_CTC_FIELDS = ("clt_multiplier", "pj_multiplier", "estagio_multiplier", "monthly_hours")


@router.get("/ctc-params")
async def get_ctc_p(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    params = await ctc_rules.get_params(db, u["company_id"])
    await db.commit()
    return {k: getattr(params, k) for k in _CTC_FIELDS}


@router.put("/ctc-params")
async def put_ctc_p(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), _p=Depends(require_module("configuracoes"))):
    """Saves the multipliers and recalculates every active employee so the dashboards reflect them at once."""
    params = await ctc_rules.get_params(db, u["company_id"])
    for key in _CTC_FIELDS:
        if key not in d:
            continue
        try:
            value = float(d[key])
        except (TypeError, ValueError):
            raise HTTPException(400, f"Valor inválido para {key}")
        if key == "monthly_hours" and not 1 <= value <= 744:
            raise HTTPException(400, "Horas por mês devem estar entre 1 e 744")
        if key != "monthly_hours" and not 1 <= value <= 5:
            raise HTTPException(400, "O multiplicador deve estar entre 1 e 5")
        setattr(params, key, value)

    employees = (await db.execute(select(EmployeeModel).where(EmployeeModel.company_id == u["company_id"], EmployeeModel.is_active == True))).scalars().all()  # noqa: E712
    for e in employees:
        ctc, hourly = ctc_rules.compute(e.base_salary or 0, e.contract_type, params)
        if ctc != e.ctc_monthly or hourly != e.hourly_cost:
            e.ctc_snapshot = e.ctc_monthly = ctc
            e.hourly_rate = e.hourly_cost = hourly
            db.add(SalaryHistoryModel(id=f"sh-{uuid.uuid4().hex[:8]}", employee_id=e.id, base_salary=e.base_salary,
                                      ctc_monthly=ctc, ctc_snapshot=ctc, changed_at=date.today().isoformat(),
                                      reason="Parâmetros de CTC atualizados"))
    audit.record_by(db, u, "CTC_ALTERADO", entity="ctc_params", details={k: getattr(params, k) for k in _CTC_FIELDS})
    await db.commit()
    return {**{k: getattr(params, k) for k in _CTC_FIELDS}, "recalculated_employees": len(employees)}
