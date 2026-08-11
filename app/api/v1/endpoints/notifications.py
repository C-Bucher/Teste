from fastapi import APIRouter, HTTPException, Depends
from app.core.security import get_current_user
from app.db.database import NOTIFICATIONS

router = APIRouter()

@router.get("/")
async def get_notifs(unread_only:bool=False,u=Depends(get_current_user)):
    n=[x for x in NOTIFICATIONS if not unread_only or not x["is_read"]]
    return {"items":n,"total":len(n),"unread_count":sum(1 for x in NOTIFICATIONS if not x["is_read"])}

@router.post("/{nid}/read")
async def mark_read(nid:str,u=Depends(get_current_user)):
    n=next((x for x in NOTIFICATIONS if x["id"]==nid),None)
    if n: n["is_read"]=True; return {"success":True}

@router.post("/{nid}/archive")
async def archive_notif(nid:str,u=Depends(get_current_user)):
    n=next((x for x in NOTIFICATIONS if x["id"]==nid),None)
    if n: n["archived"]=True; return {"success":True}
    return {"success":True}

@router.post("/read-all")
async def mark_all_read(u=Depends(get_current_user)):
    for n in NOTIFICATIONS: n["is_read"]=True
    return {"success":True}

@router.get("/unread-count")
async def notif_unread_count(u=Depends(get_current_user)):
    return {"count":sum(1 for x in NOTIFICATIONS if not x["is_read"])}

@router.get("/preferences")
async def notif_prefs(u=Depends(get_current_user)): return {"email_enabled":True,"inapp_enabled":True}

@router.put("/preferences")
async def upd_notif_prefs(d:dict,u=Depends(get_current_user)): return {"success":True,**d}
