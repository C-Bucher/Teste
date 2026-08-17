from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import bcrypt

from app.core.security import create_token, decode_token, get_current_user, bearer
from app.db.database import USERS_DB
from app.api.v1.endpoints.plans import PLANS_DB

router = APIRouter()

class LoginReq(BaseModel):
    email:str; password:str; mfa_code:Optional[str]=None

class RegisterReq(BaseModel):
    full_name: str
    email: str
    password: str
    company_name: Optional[str] = "Minha Empresa"
    cnpj_cpf: Optional[str] = None
    selected_plan: Optional[str] = "plan-empresarial"

@router.post("/register")
async def register(b: RegisterReq):
    if b.email in USERS_DB:
        raise HTTPException(400, "Este e-mail já está cadastrado no sistema")

    user_id = f"usr-{len(USERS_DB) + 1:03d}"
    pwd_hash = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()

    plan = next((p for p in PLANS_DB if p["id"] == b.selected_plan), None)
    plan_scope = plan["scope"] if plan else "completo"

    new_user = {
        "id": user_id,
        "email": b.email,
        "full_name": b.full_name,
        "role": "ADMIN",
        "company_name": b.company_name,
        "selected_plan": b.selected_plan,
        "plan_scope": plan_scope,
        "password_hash": pwd_hash,
        "is_active": True,
        "mfa_enabled": False
    }
    USERS_DB[b.email] = new_user

    tok = create_token(new_user)
    return {
        "access_token": tok,
        "refresh_token": tok,
        "token_type": "bearer",
        "user": {k: v for k, v in new_user.items() if k != "password_hash"}
    }

@router.post("/login")
async def login(b:LoginReq):
    u=USERS_DB.get(b.email)
    if not u or not bcrypt.checkpw(b.password.encode(),u["password_hash"].encode()):
        raise HTTPException(401,"Credenciais invalidas")
    tok=create_token(u)
    return {"access_token":tok,"refresh_token":tok,"token_type":"bearer","user":{k:v for k,v in u.items() if k!="password_hash"}}

@router.get("/me")
async def me(u=Depends(get_current_user)):
    return {k:v for k,v in u.items() if k!="password_hash"}

@router.post("/logout")
async def logout(u=Depends(get_current_user)): return {"message":"Logout realizado"}

class RefreshReq(BaseModel):
    refresh_token:Optional[str]=None

@router.post("/refresh")
async def refresh(b:RefreshReq=RefreshReq(),creds:HTTPAuthorizationCredentials=Depends(bearer)):
    token=b.refresh_token or (creds.credentials if creds else None)
    if not token: raise HTTPException(401,"Token ausente")
    p=decode_token(token)
    u=USERS_DB.get(p.get("email")) or next((v for v in USERS_DB.values() if v["id"]==p.get("sub")),None)
    if not u: raise HTTPException(401,"Usuario nao encontrado")
    tok=create_token(u)
    return {"access_token":tok,"refresh_token":tok,"token_type":"bearer"}

@router.get("/users")
async def get_auth_users(u=Depends(get_current_user)): return [{k:v for k,v in x.items() if k!="password_hash"} for x in USERS_DB.values()]

@router.put("/users/{uid}")
async def upd_auth_user(uid:str,d:dict,u=Depends(get_current_user)):
    usr=next((v for v in USERS_DB.values() if v["id"]==uid),None)
    if not usr: raise HTTPException(404)
    usr.update({k:v for k,v in d.items() if k!="password_hash"}); return {k:v for k,v in usr.items() if k!="password_hash"}
