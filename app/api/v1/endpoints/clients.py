from fastapi import APIRouter, HTTPException, Depends
import uuid
from app.core.security import get_current_user
from app.db.database import KANBAN_CLIENTS

router = APIRouter()

@router.get("/")
async def get_clients(u=Depends(get_current_user)): return KANBAN_CLIENTS
@router.post("/")
async def create_client(d:dict,u=Depends(get_current_user)):
    c={"id":f"cli-{uuid.uuid4().hex[:6]}",**d}; KANBAN_CLIENTS.append(c); return c
@router.put("/{cid}")
async def upd_client(cid:str,d:dict,u=Depends(get_current_user)):
    c=next((x for x in KANBAN_CLIENTS if x["id"]==cid),None)
    if not c:
        raise HTTPException(404)
    c.update(d)
    return c
@router.delete("/{cid}")
async def del_client(cid:str,u=Depends(get_current_user)):
    global KANBAN_CLIENTS
    KANBAN_CLIENTS[:]=[x for x in KANBAN_CLIENTS if x["id"]!=cid]; return {"success":True}
