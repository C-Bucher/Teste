from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import NotificationModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

@router.get("/")
async def get_notifs(unread_only:bool=False,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(NotificationModel))
    all_notifs=result.scalars().all()
    n=[x for x in all_notifs if not unread_only or not x.is_read]
    return {"items":models_to_dicts(n),"total":len(n),"unread_count":sum(1 for x in all_notifs if not x.is_read)}

@router.post("/{nid}/read")
async def mark_read(nid:str,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    n=await db.get(NotificationModel,nid)
    if n:
        n.is_read=True
        await db.commit()
        return {"success":True}

@router.post("/{nid}/archive")
async def archive_notif(nid:str,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    n=await db.get(NotificationModel,nid)
    # NotificationModel has no "archived" column (mock-only field); no-op persistence, same as before.
    return {"success":True}

@router.post("/read-all")
async def mark_all_read(u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(NotificationModel))
    for n in result.scalars().all():
        n.is_read=True
    await db.commit()
    return {"success":True}

@router.get("/unread-count")
async def notif_unread_count(u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(NotificationModel).where(NotificationModel.is_read==False))
    return {"count":len(result.scalars().all())}

@router.get("/preferences")
async def notif_prefs(u=Depends(get_current_user)): return {"email_enabled":True,"inapp_enabled":True}

@router.put("/preferences")
async def upd_notif_prefs(d:dict,u=Depends(get_current_user)): return {"success":True,**d}
