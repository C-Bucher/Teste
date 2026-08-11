from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime, date, timedelta
import random
from app.core.security import get_current_user
from app.db.database import FINANCIAL_ENTRIES, hoje, dias

router = APIRouter()

@router.get("/entries")
async def get_entries(skip:int=0,size:int=50,page:int=1,type:Optional[str]=None,status:Optional[str]=None,search:Optional[str]=None,category:Optional[str]=None,u=Depends(get_current_user)):
    e=FINANCIAL_ENTRIES[:]
    if type: e=[x for x in e if x["type"]==type]
    if status: e=[x for x in e if x["status"]==status]
    if category: e=[x for x in e if x.get("category","").lower()==category.lower()]
    if search:
        s=search.lower()
        e=[x for x in e if s in x.get("description","").lower() or s in x.get("category","").lower() or s in x.get("cost_center","").lower()]
    if page>1: skip=(page-1)*size
    total=len(e)
    return {"items":e[skip:skip+size],"total":total,"page":page,"size":size,"pages":(total+size-1)//size}

@router.post("/entries")
async def create_entry(d:dict,u=Depends(get_current_user)):
    en={"id":f"fin-{uuid.uuid4().hex[:6]}","status":"PENDENTE","payment_date":None,**d}
    FINANCIAL_ENTRIES.append(en); return en

@router.get("/entries/{eid}")
async def get_entry(eid:str,u=Depends(get_current_user)):
    e=next((x for x in FINANCIAL_ENTRIES if x["id"]==eid),None)
    if not e:
        raise HTTPException(404)
    return e

@router.put("/entries/{eid}")
async def upd_entry(eid:str,d:dict,u=Depends(get_current_user)):
    e=next((x for x in FINANCIAL_ENTRIES if x["id"]==eid),None)
    if not e:
        raise HTTPException(404)
    e.update(d)
    return e

@router.post("/entries/{eid}/pay")
async def pay_entry(eid:str,u=Depends(get_current_user)):
    e=next((x for x in FINANCIAL_ENTRIES if x["id"]==eid),None)
    if not e: raise HTTPException(404)
    e["status"]="PAGO"; e["payment_date"]=date.today().isoformat(); return e

@router.post("/entries/{eid}/attachment")
async def attach(eid:str,u=Depends(get_current_user)): return {"attachment_url":f"/uploads/{eid}.pdf"}

@router.get("/dre")
async def get_dre(start_date:Optional[str]=None,end_date:Optional[str]=None,start:Optional[str]=None,end:Optional[str]=None,u=Depends(get_current_user)):
    rec=sum(e["amount"] for e in FINANCIAL_ENTRIES if e["type"]=="RECEITA")
    desp=sum(e["amount"] for e in FINANCIAL_ENTRIES if e["type"]=="DESPESA")
    receitas_list=[{"categoria":"Desenvolvimento","total":28500.0},{"categoria":"Consultoria","total":15000.0},{"categoria":"Suporte","total":17000.0},{"categoria":"SaaS","total":42000.0}]
    despesas_list=[{"categoria":"Pessoal","total":8500.0},{"categoria":"Infraestrutura","total":4200.0},{"categoria":"Aluguel","total":3500.0},{"categoria":"Ferramentas","total":1140.0},{"categoria":"Contabilidade","total":2800.0}]
    return {"period":{"start":start_date or start or dias(-30),"end":end_date or end or dias(0)},"total_receitas":round(rec,2),"total_despesas":round(desp,2),"receitas":receitas_list,"despesas":despesas_list,"resultado_liquido":round(rec-desp,2),"margem_percentual":round((rec-desp)/rec*100,1) if rec else 0}

@router.get("/cashflow")
async def get_cashflow(u=Depends(get_current_user)):
    random.seed(42); saldo=48000.0; items=[]
    for i in range(-30,61):
        d=hoje+timedelta(days=i)
        rec=random.uniform(0,12000) if d.weekday()<5 else 0
        desp=random.uniform(0,6000) if d.weekday()<5 else 0
        if d.day==5: rec+=28500
        if d.day==10: desp+=8500
        if d.day==15: rec+=15000
        if d.day==20: desp+=3500
        saldo+=rec-desp
        items.append({"date":d.isoformat(),"receitas":round(rec,2),"despesas":round(desp,2),"saldo_acumulado":round(saldo,2)})
    return {
        "items":items,
        "saldo_atual":48000.0,
        "current_balance":48000.0,
        "receitas_previstas_30d":72000.0,
        "projected_income":72000.0,
        "despesas_previstas_30d":31500.0,
        "projected_expense":31500.0,
        "projected_balance":40500.0,
        "alert_level":"VERDE",
        "generated_at":datetime.now().isoformat(),
    }
