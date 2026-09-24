from fastapi import APIRouter, HTTPException, Depends
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core.permissions import require_module
from app.db.session import get_db
from app.db.models import CompanyModel, CostCenterModel, CategoryModel, WorkCalendarModel
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

@router.get("/work-calendar")
async def get_cal(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return model_to_dict(await _calendar(db, u["company_id"]))
@router.get("/calendar")
async def get_cal2(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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

@router.get("/ctc-params")
async def get_ctc_p(u=Depends(get_current_user)): return [{"id":"p-001","contract_type":"CLT","inss_rate":0.20,"fgts_rate":0.08,"ferias_rate":0.1111,"decimo_rate":0.0833},{"id":"p-002","contract_type":"PJ","iss_rate":0.05},{"id":"p-003","contract_type":"ESTAGIO","seguro_rate":0.02}]
@router.post("/logo")
async def logo(u=Depends(get_current_user)):
    raise HTTPException(501, "Upload de logotipo ainda não implementado")
