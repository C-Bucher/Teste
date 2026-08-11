from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
import time
from datetime import datetime
from app.core.security import get_current_user
from app.db.database import KANBAN_CLIENTS, KANBAN_PROJECTS, KANBAN_BOARDS, ACTIVE_TIMERS, EMPLOYEES

router = APIRouter()

@router.get("/templates")
async def get_kanban_templates(u=Depends(get_current_user)): return []

@router.get("/clients")
async def get_clis(u=Depends(get_current_user)): return KANBAN_CLIENTS
@router.post("/clients")
async def create_cli(d:dict,u=Depends(get_current_user)):
    c={"id":f"cli-{uuid.uuid4().hex[:6]}",**d}; KANBAN_CLIENTS.append(c); return c
@router.put("/clients/{cid}")
async def upd_cli(cid:str,d:dict,u=Depends(get_current_user)):
    c=next((x for x in KANBAN_CLIENTS if x["id"]==cid),None)
    if not c:
        raise HTTPException(404)
    c.update(d)
    return c

@router.get("/projects")
async def get_projs(client_id:Optional[str]=None,u=Depends(get_current_user)):
    p=KANBAN_PROJECTS if not client_id else [x for x in KANBAN_PROJECTS if x["client_id"]==client_id]
    return p
@router.post("/projects")
async def create_proj(d:dict,u=Depends(get_current_user)):
    p={"id":f"proj-{uuid.uuid4().hex[:6]}","status":"PLANEJAMENTO",**d}
    KANBAN_PROJECTS.append(p)
    KANBAN_BOARDS[p["id"]]={"columns":[{"id":f"col-{uuid.uuid4().hex[:4]}","name":"Backlog","order":1,"cards":[]},{"id":f"col-{uuid.uuid4().hex[:4]}","name":"Em Andamento","order":2,"cards":[]},{"id":f"col-{uuid.uuid4().hex[:4]}","name":"Concluido","order":3,"cards":[]}]}
    return p
@router.get("/projects/{pid}/board")
async def get_board(pid:str,u=Depends(get_current_user)):
    b=KANBAN_BOARDS.get(pid,{"columns":[]})
    proj=next((p for p in KANBAN_PROJECTS if p["id"]==pid),None)
    cli=next((c for c in KANBAN_CLIENTS if proj and c["id"]==proj.get("client_id")),None)
    return {"project":proj,"client":cli,**b}
@router.post("/projects/{pid}/columns")
async def add_col(pid:str,d:dict,u=Depends(get_current_user)):
    b=KANBAN_BOARDS.setdefault(pid,{"columns":[]})
    col={"id":f"col-{uuid.uuid4().hex[:6]}","order":len(b["columns"])+1,"cards":[],**d}
    b["columns"].append(col); return col

@router.post("/cards")
async def create_card(d:dict,u=Depends(get_current_user)):
    e=next((x for x in EMPLOYEES if x["id"]==d.get("assignee_id")),None)
    card={"id":f"card-{uuid.uuid4().hex[:6]}","cost_per_task":0,"total_time_seconds":0,"ctc_snapshot":e["hourly_rate"] if e else 0,"status":"ABERTO",**d}
    col_id=d.get("column_id")
    for brd in KANBAN_BOARDS.values():
        for col in brd.get("columns",[]):
            if col["id"]==col_id: col["cards"].append(card); return card
    return card
@router.post("/cards/{cid}/move")
async def move_card(cid:str,d:dict,u=Depends(get_current_user)):
    new_col=d.get("column_id"); card_obj=None
    for brd in KANBAN_BOARDS.values():
        for col in brd.get("columns",[]):
            for c in col["cards"]:
                if c["id"]==cid: card_obj=c; col["cards"].remove(c); break
            if card_obj: break
        if card_obj: break
    if card_obj and new_col:
        for brd in KANBAN_BOARDS.values():
            for col in brd.get("columns",[]):
                if col["id"]==new_col: col["cards"].append(card_obj); break
    return {"id":cid,"column_id":new_col,"moved":True}
@router.put("/cards/{cid}")
async def upd_card(cid:str,d:dict,u=Depends(get_current_user)):
    for brd in KANBAN_BOARDS.values():
        for col in brd.get("columns",[]):
            for c in col["cards"]:
                if c["id"]==cid: c.update(d); return c
    raise HTTPException(404)
@router.delete("/cards/{cid}")
async def del_card(cid:str,u=Depends(get_current_user)):
    for brd in KANBAN_BOARDS.values():
        for col in brd.get("columns",[]):
            col["cards"]=[c for c in col["cards"] if c["id"]!=cid]
    return {"success":True}

@router.post("/cards/{cid}/time/start")
async def start_timer(cid:str,u=Depends(get_current_user)):
    ACTIVE_TIMERS[cid]={"started_at":time.time(),"employee_id":u["id"],"timer_id":f"tmr-{uuid.uuid4().hex[:8]}"}
    return {"card_id":cid,"started_at":datetime.now().isoformat()}
@router.post("/cards/{cid}/time/stop")
async def stop_timer(cid:str,u=Depends(get_current_user)):
    t=ACTIVE_TIMERS.pop(cid,None); elapsed=int(time.time()-t["started_at"]) if t else 3600
    for brd in KANBAN_BOARDS.values():
        for col in brd.get("columns",[]):
            for c in col["cards"]:
                if c["id"]==cid:
                    c["total_time_seconds"]=c.get("total_time_seconds",0)+elapsed
                    emp=next((e for e in EMPLOYEES if e["id"]==c.get("assignee_id")),None)
                    c["cost_per_task"]=round(c["total_time_seconds"]/3600*(emp["hourly_rate"] if emp else 85),2)
    return {"card_id":cid,"total_time_seconds":elapsed,"cost_per_task":round(elapsed/3600*85,2)}
@router.post("/cards/{cid}/timer/start")
async def start_timer2(cid:str,employee_id:Optional[str]=None,u=Depends(get_current_user)):
    tid=f"tmr-{uuid.uuid4().hex[:8]}"
    ACTIVE_TIMERS[cid]={"started_at":time.time(),"employee_id":employee_id or u["id"],"timer_id":tid}
    return {"card_id":cid,"started_at":datetime.now().isoformat(),"timerId":tid}
@router.post("/cards/{cid}/timer/stop")
async def stop_timer2(cid:str,u=Depends(get_current_user)):
    return await stop_timer(cid, u)

@router.post("/cards/{cid}/comments")
async def add_comment(cid:str,d:dict,u=Depends(get_current_user)): 
    return {"id":f"cmt-{uuid.uuid4().hex[:6]}","card_id":cid,"author":u["full_name"],"content":d.get("content"),"created_at":datetime.now().isoformat()}
