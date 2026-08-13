from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import date
from app.core.security import get_current_user
from app.db.database import PERSONAL_ENTRIES, PERSONAL_ACCOUNTS, PERSONAL_BUDGETS, PERSONAL_GOALS, PERSONAL_DEBTS, PERSONAL_SUBSCRIPTIONS, PERSONAL_SPLITS, PERSONAL_TIMEBOXES, PERSONAL_OKRS

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
async def get_timeboxes(u=Depends(get_current_user)): return PERSONAL_TIMEBOXES
@router.post("/timeboxes")
async def create_timebox(d:dict,u=Depends(get_current_user)):
    tb={"id":f"ptb-{uuid.uuid4().hex[:6]}",**d}; PERSONAL_TIMEBOXES.append(tb); return tb

@router.get("/okrs")
async def get_okrs(u=Depends(get_current_user)): return PERSONAL_OKRS
@router.post("/okrs")
async def create_okr(d:dict,u=Depends(get_current_user)):
    okr={"id":f"pokr-{uuid.uuid4().hex[:6]}",**d}; PERSONAL_OKRS.append(okr); return okr

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
@router.delete("/entries/{eid}")
async def del_pers(eid:str,u=Depends(get_current_user)):
    global PERSONAL_ENTRIES
    PERSONAL_ENTRIES[:]=[x for x in PERSONAL_ENTRIES if x["id"]!=eid]; return {"success":True}

@router.get("/accounts")
async def get_accounts(u=Depends(get_current_user)): return PERSONAL_ACCOUNTS
@router.post("/accounts")
async def create_account(d:dict,u=Depends(get_current_user)):
    a={"id":f"pacc-{uuid.uuid4().hex[:6]}",**d}; PERSONAL_ACCOUNTS.append(a); return a
@router.delete("/accounts/{aid}")
async def del_account(aid:str,u=Depends(get_current_user)):
    global PERSONAL_ACCOUNTS
    PERSONAL_ACCOUNTS[:]=[x for x in PERSONAL_ACCOUNTS if x["id"]!=aid]; return {"success":True}

@router.get("/budgets")
async def get_budgets(u=Depends(get_current_user)): return PERSONAL_BUDGETS
@router.post("/budgets")
async def create_budget(d:dict,u=Depends(get_current_user)):
    b={"id":f"pbud-{uuid.uuid4().hex[:6]}","spent_amount":0.0,**d}; PERSONAL_BUDGETS.append(b); return b
@router.delete("/budgets/{bid}")
async def del_budget(bid:str,u=Depends(get_current_user)):
    global PERSONAL_BUDGETS
    PERSONAL_BUDGETS[:]=[x for x in PERSONAL_BUDGETS if x["id"]!=bid]; return {"success":True}

@router.get("/goals")
async def get_goals(u=Depends(get_current_user)): return PERSONAL_GOALS
@router.post("/goals")
async def create_goal(d:dict,u=Depends(get_current_user)):
    g={"id":f"pgoal-{uuid.uuid4().hex[:6]}","current_amount":0.0,**d}; PERSONAL_GOALS.append(g); return g
@router.post("/goals/{gid}/contribute")
async def contribute_goal(gid:str,d:dict,u=Depends(get_current_user)):
    g=next((x for x in PERSONAL_GOALS if x["id"]==gid),None)
    if not g: raise HTTPException(404)
    g["current_amount"]=round(g["current_amount"]+d.get("amount",0),2); return g
@router.delete("/goals/{gid}")
async def del_goal(gid:str,u=Depends(get_current_user)):
    global PERSONAL_GOALS
    PERSONAL_GOALS[:]=[x for x in PERSONAL_GOALS if x["id"]!=gid]; return {"success":True}

@router.get("/debts")
async def get_debts(u=Depends(get_current_user)): return PERSONAL_DEBTS
@router.post("/debts")
async def create_debt(d:dict,u=Depends(get_current_user)):
    deb={"id":f"pdebt-{uuid.uuid4().hex[:6]}","installments_paid":0,**d}; PERSONAL_DEBTS.append(deb); return deb
@router.delete("/debts/{did}")
async def del_debt(did:str,u=Depends(get_current_user)):
    global PERSONAL_DEBTS
    PERSONAL_DEBTS[:]=[x for x in PERSONAL_DEBTS if x["id"]!=did]; return {"success":True}

@router.get("/subscriptions")
async def get_subs(u=Depends(get_current_user)): return PERSONAL_SUBSCRIPTIONS
@router.post("/subscriptions")
async def create_sub(d:dict,u=Depends(get_current_user)):
    s={"id":f"psub-{uuid.uuid4().hex[:6]}","is_active":True,**d}; PERSONAL_SUBSCRIPTIONS.append(s); return s
@router.delete("/subscriptions/{sid}")
async def del_sub(sid:str,u=Depends(get_current_user)):
    global PERSONAL_SUBSCRIPTIONS
    PERSONAL_SUBSCRIPTIONS[:]=[x for x in PERSONAL_SUBSCRIPTIONS if x["id"]!=sid]; return {"success":True}

@router.get("/splits")
async def get_splits(u=Depends(get_current_user)): return PERSONAL_SPLITS
@router.post("/splits")
async def create_split(d:dict,u=Depends(get_current_user)):
    sp={"id":f"psplit-{uuid.uuid4().hex[:6]}",**d}; PERSONAL_SPLITS.append(sp); return sp
@router.delete("/splits/{spid}")
async def del_split(spid:str,u=Depends(get_current_user)):
    global PERSONAL_SPLITS
    PERSONAL_SPLITS[:]=[x for x in PERSONAL_SPLITS if x["id"]!=spid]; return {"success":True}

@router.get("/analytics")
async def get_analytics(u=Depends(get_current_user)):
    total_by_cat: dict = {}
    for e in PERSONAL_ENTRIES:
        if e["type"] == "DESPESA":
            total_by_cat[e["category"]] = total_by_cat.get(e["category"], 0) + e["amount"]
    net_worth_series = [{"month": m, "value": 8000 + i * 650} for i, m in enumerate(["Mar","Abr","Mai","Jun","Jul","Ago"])]
    return {"spend_by_category": [{"category": k, "total": round(v, 2)} for k, v in total_by_cat.items()], "net_worth_series": net_worth_series}

@router.post("/ai/insights")
async def personal_ai_insights(d:dict,u=Depends(get_current_user)):
    return {"insights": [
        {"type": "ALERT", "message": "Seus gastos com Lazer estão em 97% do orçamento mensal.", "impact_value": 390.00},
        {"type": "OPPORTUNITY", "message": "Você poderia render R$ 42/mês a mais movendo sua reserva para um CDB de liquidez diária.", "impact_value": 42.00},
        {"type": "CUT", "message": "Você tem 2 assinaturas ativas (Netflix, Academia) somando R$ 139,80/mês.", "impact_value": 139.80},
    ]}
