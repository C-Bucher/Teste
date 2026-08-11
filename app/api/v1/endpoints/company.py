from fastapi import APIRouter, HTTPException, Depends
import uuid
from app.core.security import get_current_user
from app.db.database import COMPANY, COST_CENTERS, CATEGORIES

router = APIRouter()

@router.get("/")
async def get_company(u=Depends(get_current_user)): return COMPANY
@router.put("/")
async def upd_company(d:dict,u=Depends(get_current_user)): COMPANY.update(d); return COMPANY

@router.get("/cost-centers")
async def get_cc(u=Depends(get_current_user)): return COST_CENTERS
@router.post("/cost-centers")
async def create_cc(d:dict,u=Depends(get_current_user)):
    cc={"id":f"cc-{uuid.uuid4().hex[:6]}",**d}; COST_CENTERS.append(cc); return cc
@router.delete("/cost-centers/{cid}")
async def del_cc(cid:str,u=Depends(get_current_user)):
    global COST_CENTERS
    COST_CENTERS=[x for x in COST_CENTERS if x["id"]!=cid]; return {"success":True}

@router.get("/categories")
async def get_cats(u=Depends(get_current_user)): return CATEGORIES
@router.post("/categories")
async def create_cat(d:dict,u=Depends(get_current_user)):
    c={"id":f"cat-{uuid.uuid4().hex[:6]}",**d}; CATEGORIES.append(c); return c

@router.get("/work-calendar")
async def get_cal(u=Depends(get_current_user)): return {"work_days":[1,2,3,4,5],"work_hours_per_day":8}
@router.get("/calendar")
async def get_cal2(u=Depends(get_current_user)): return {"work_days":[1,2,3,4,5],"work_hours_per_day":8,"holidays":[]}
@router.put("/calendar")
async def upd_calendar(d:dict,u=Depends(get_current_user)): return {"work_days":[1,2,3,4,5],"work_hours_per_day":8,**d}

@router.get("/ctc-params")
async def get_ctc_p(u=Depends(get_current_user)): return [{"id":"p-001","contract_type":"CLT","inss_rate":0.20,"fgts_rate":0.08,"ferias_rate":0.1111,"decimo_rate":0.0833},{"id":"p-002","contract_type":"PJ","iss_rate":0.05},{"id":"p-003","contract_type":"ESTAGIO","seguro_rate":0.02}]
@router.post("/logo")
async def logo(u=Depends(get_current_user)): return {"logo_url":"/uploads/logo.png"}
