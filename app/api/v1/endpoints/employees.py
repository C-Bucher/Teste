from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import date
import uuid
from app.core.security import get_current_user
from app.db.database import EMPLOYEES

router = APIRouter()

@router.get("/")
async def get_emps(skip:int=0,limit:int=100,active:Optional[bool]=None,search:Optional[str]=None,contract_type:Optional[str]=None,department:Optional[str]=None,u=Depends(get_current_user)):
    e=[x for x in EMPLOYEES if active is None or x["is_active"]==active]
    if search:
        s=search.lower()
        e=[x for x in e if s in x.get("full_name","").lower() or s in x.get("role","").lower() or s in x.get("email","").lower() or s in x.get("position","").lower()]
    if contract_type: e=[x for x in e if x.get("contract_type")==contract_type]
    if department: e=[x for x in e if department.lower() in x.get("role","").lower()]
    return e[skip:skip+limit]

@router.post("/")
async def create_emp(d:dict,u=Depends(get_current_user)):
    base=d.get("base_salary",0); ctc=base*1.75 if d.get("contract_type")=="CLT" else base*1.1
    hr=round(ctc/176,2)
    emp={"id":f"emp-{uuid.uuid4().hex[:6]}","ctc_snapshot":round(ctc,2),"ctc_monthly":round(ctc,2),"hourly_rate":hr,"hourly_cost":hr,"is_active":True,"position":d.get("role",""),"hire_date":d.get("start_date",date.today().isoformat()),**d}
    EMPLOYEES.append(emp); return emp

@router.get("/{eid}")
async def get_emp(eid:str,u=Depends(get_current_user)):
    e=next((x for x in EMPLOYEES if x["id"]==eid),None)
    if not e:
        raise HTTPException(404)
    return e

@router.put("/{eid}")
async def upd_emp(eid:str,d:dict,u=Depends(get_current_user)):
    e=next((x for x in EMPLOYEES if x["id"]==eid),None)
    if not e:
        raise HTTPException(404)
    e.update(d)
    return e

@router.delete("/{eid}")
async def del_emp(eid:str,u=Depends(get_current_user)):
    e=next((x for x in EMPLOYEES if x["id"]==eid),None)
    if not e: raise HTTPException(404)
    e["is_active"]=False; e["end_date"]=date.today().isoformat(); return {"success":True}

@router.post("/{eid}/terminate")
async def term_emp(eid:str,u=Depends(get_current_user)):
    e=next((x for x in EMPLOYEES if x["id"]==eid),None)
    if not e: raise HTTPException(404)
    e["is_active"]=False; e["end_date"]=date.today().isoformat(); return e

@router.get("/{eid}/salary-history")
async def sal_hist(eid:str,u=Depends(get_current_user)):
    e=next((x for x in EMPLOYEES if x["id"]==eid),None)
    if not e: raise HTTPException(404)
    return {"items":[{"id":"sh-001","employee_id":eid,"base_salary":e["base_salary"]-500,"ctc_monthly":e["ctc_monthly"]-875,"ctc_snapshot":e["ctc_snapshot"]-875,"changed_at":"2025-09-01","reason":"Reajuste anual"},{"id":"sh-002","employee_id":eid,"base_salary":e["base_salary"],"ctc_monthly":e["ctc_monthly"],"ctc_snapshot":e["ctc_snapshot"],"changed_at":"2026-01-01","reason":"Promocao"}]}
