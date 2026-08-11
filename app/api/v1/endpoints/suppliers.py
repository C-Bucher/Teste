from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
from app.core.security import get_current_user
from app.db.database import SUPPLIERS

router = APIRouter()

@router.get("/")
async def get_sups(active_only:Optional[bool]=None,u=Depends(get_current_user)):
    s=SUPPLIERS if active_only is None else [x for x in SUPPLIERS if x["is_active"]==active_only]
    return s
@router.post("/")
async def create_sup(d:dict,u=Depends(get_current_user)):
    s={"id":f"sup-{uuid.uuid4().hex[:6]}","is_active":True,**d}; SUPPLIERS.append(s); return s
@router.delete("/{sid}")
async def del_sup(sid:str,u=Depends(get_current_user)):
    global SUPPLIERS
    SUPPLIERS[:] = [x for x in SUPPLIERS if x["id"]!=sid]
    return {"success":True}
@router.get("/{sid}")
async def get_sup(sid:str,u=Depends(get_current_user)):
    s=next((x for x in SUPPLIERS if x["id"]==sid),None)
    if not s:
        raise HTTPException(404)
    return s
@router.put("/{sid}")
async def upd_sup(sid:str,d:dict,u=Depends(get_current_user)):
    s=next((x for x in SUPPLIERS if x["id"]==sid),None)
    if not s:
        raise HTTPException(404)
    s.update(d)
    return s
