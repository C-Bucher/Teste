from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import date
from app.core.security import get_current_user
from app.db.database import PERSONAL_ENTRIES

router = APIRouter()

@router.get("/transactions")
async def get_pers_tx(u=Depends(get_current_user)): return PERSONAL_ENTRIES
@router.post("/transactions")
async def create_pers_tx(d:dict,u=Depends(get_current_user)):
    e={"id":f"pes-{uuid.uuid4().hex[:6]}","date":date.today().isoformat(),**d}; PERSONAL_ENTRIES.append(e); return e
@router.delete("/transactions/{eid}")
async def del_pers_tx(eid:str,u=Depends(get_current_user)):
    global PERSONAL_ENTRIES
    PERSONAL_ENTRIES[:]=[x for x in PERSONAL_ENTRIES if x["id"]!=eid]; return {"success":True}

@router.get("/categories")
async def get_pers_cats(u=Depends(get_current_user)): return [{"id":"pc-1","name":"Salario","type":"RECEITA"},{"id":"pc-2","name":"Moradia","type":"DESPESA"},{"id":"pc-3","name":"Alimentacao","type":"DESPESA"},{"id":"pc-4","name":"Saude","type":"DESPESA"}]

@router.get("/timeboxes")
async def get_timeboxes(u=Depends(get_current_user)): return []
@router.post("/timeboxes")
async def create_timebox(d:dict,u=Depends(get_current_user)): return {"id":f"tb-{uuid.uuid4().hex[:6]}",**d}

@router.get("/okrs")
async def get_okrs(u=Depends(get_current_user)): return []
@router.post("/okrs")
async def create_okr(d:dict,u=Depends(get_current_user)): return {"id":f"okr-{uuid.uuid4().hex[:6]}",**d}

@router.get("/dashboard")
async def pers_dash(u=Depends(get_current_user)):
    rec=sum(e["amount"] for e in PERSONAL_ENTRIES if e["type"]=="RECEITA")
    desp=sum(e["amount"] for e in PERSONAL_ENTRIES if e["type"]=="DESPESA")
    return {"saldo":round(rec-desp,2),"balance":round(rec-desp,2),"receitas_mes":rec,"total_income":rec,"despesas_mes":desp,"total_expense":desp,"recent_entries":PERSONAL_ENTRIES}

@router.get("/entries")
async def get_pers(u=Depends(get_current_user)): return {"items":PERSONAL_ENTRIES,"total":len(PERSONAL_ENTRIES)}
@router.post("/entries")
async def create_pers(d:dict,u=Depends(get_current_user)):
    e={"id":f"pes-{uuid.uuid4().hex[:6]}","date":date.today().isoformat(),**d}; PERSONAL_ENTRIES.append(e); return e
