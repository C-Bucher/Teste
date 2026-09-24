from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import NotificationModel, NotificationPreferenceModel
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

@router.get("/")
async def get_notifs(unread_only:bool=False,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(NotificationModel).where(NotificationModel.company_id == u["company_id"], NotificationModel.is_archived == False))
    all_notifs=result.scalars().all()
    n=[x for x in all_notifs if not unread_only or not x.is_read]
    return {"items":models_to_dicts(n),"total":len(n),"unread_count":sum(1 for x in all_notifs if not x.is_read)}

@router.post("/{nid}/read")
async def mark_read(nid:str,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    n=await db.get(NotificationModel,nid)
    if not n or n.company_id != u["company_id"]:
        raise HTTPException(404)
    n.is_read=True
    await db.commit()
    return {"success":True}

@router.post("/{nid}/archive")
async def archive_notif(nid:str,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    n=await db.get(NotificationModel,nid)
    if not n or n.company_id != u["company_id"]:
        raise HTTPException(404)
    n.is_archived=True
    await db.commit()
    return {"success":True}

@router.post("/read-all")
async def mark_all_read(u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(NotificationModel).where(NotificationModel.company_id == u["company_id"], NotificationModel.is_archived == False))
    for n in result.scalars().all():
        n.is_read=True
    await db.commit()
    return {"success":True}

@router.get("/unread-count")
async def notif_unread_count(u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result=await db.execute(select(NotificationModel).where(NotificationModel.company_id == u["company_id"], NotificationModel.is_read==False, NotificationModel.is_archived == False))
    return {"count":len(result.scalars().all())}

async def _prefs(user_id: str, db: AsyncSession) -> NotificationPreferenceModel:
    prefs = await db.get(NotificationPreferenceModel, user_id)
    if prefs is None:
        prefs = NotificationPreferenceModel(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs

@router.get("/preferences")
async def notif_prefs(u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    return model_to_dict(await _prefs(u["id"], db))

@router.put("/preferences")
async def upd_notif_prefs(d:dict,u=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    prefs = await _prefs(u["id"], db)
    for key in ("email_enabled", "inapp_enabled"):
        if key in d:
            setattr(prefs, key, bool(d[key]))
    await db.commit()
    await db.refresh(prefs)
    return {"success":True, **model_to_dict(prefs)}
