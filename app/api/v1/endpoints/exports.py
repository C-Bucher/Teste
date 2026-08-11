from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime
from app.core.security import get_current_user
from app.db.database import EXPORT_LOGS

router = APIRouter()

@router.get("/")
async def get_exports_main(u=Depends(get_current_user)): return EXPORT_LOGS
@router.post("/request")
async def req_export(d:dict,u=Depends(get_current_user)):
    ex={"id":f"exp-{uuid.uuid4().hex[:6]}","status":"PROCESSANDO","created_at":datetime.now().isoformat(),**d}; EXPORT_LOGS.append(ex); return ex
@router.get("/logs")
async def get_exports(u=Depends(get_current_user)): return EXPORT_LOGS
@router.get("/download/{eid}")
async def dl_export(eid:str,u=Depends(get_current_user)): return {"download_url":f"/uploads/export_{eid}.pdf","expires_in":3600}
