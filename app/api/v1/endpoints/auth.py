from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import bcrypt

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.core.security import create_token, decode_token, get_current_user, bearer
from app.db.session import get_db
from app.db.models import UserModel, CompanyModel
from app.db.utils import model_to_dict
from app.api.v1.endpoints.plans import PLANS_DB

router = APIRouter()

_USER_COLUMNS = {c.name for c in UserModel.__table__.columns}

class LoginReq(BaseModel):
    email:str; password:str; mfa_code:Optional[str]=None

class RegisterReq(BaseModel):
    full_name: str
    email: str
    password: str
    company_name: Optional[str] = "Minha Empresa"
    cnpj_cpf: Optional[str] = None
    selected_plan: Optional[str] = "plan-empresarial"

class CreateUserReq(BaseModel):
    full_name: str
    email: str
    password: str
    role: str

@router.post("/register")
async def register(b: RegisterReq, db: AsyncSession = Depends(get_db)):
    email = b.email.strip().lower()
    existing = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Este e-mail já está cadastrado no sistema")

    company_count = (await db.execute(select(func.count()).select_from(CompanyModel))).scalar() or 0
    company_id = f"cmp-{company_count + 1:03d}"
    db.add(CompanyModel(id=company_id, name=b.company_name or "Minha Empresa"))

    user_count = (await db.execute(select(func.count()).select_from(UserModel))).scalar() or 0
    user_id = f"usr-{user_count + 1:03d}"
    pwd_hash = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()

    plan = next((p for p in PLANS_DB if p["id"] == b.selected_plan), None)
    plan_scope = plan["scope"] if plan else "completo"

    new_user = UserModel(
        id=user_id,
        company_id=company_id,
        email=email,
        full_name=b.full_name,
        role="ADMIN",
        plan_scope=plan_scope,
        password_hash=pwd_hash,
        is_active=True,
        mfa_enabled=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # company_name/selected_plan have no column on UserModel (schema gap, see task report) -
    # echoed back from the request so the response contract stays identical, not persisted.
    user_dict = model_to_dict(new_user)
    user_dict["company_name"] = b.company_name
    user_dict["selected_plan"] = b.selected_plan

    tok = create_token(user_dict)
    return {
        "access_token": tok,
        "refresh_token": tok,
        "token_type": "bearer",
        "user": {k: v for k, v in user_dict.items() if k != "password_hash"}
    }

@router.post("/login")
async def login(b: LoginReq, db: AsyncSession = Depends(get_db)):
    email = b.email.strip().lower()
    u = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if not u or not bcrypt.checkpw(b.password.encode(), u.password_hash.encode()):
        raise HTTPException(401, "Credenciais invalidas")
    user_dict = model_to_dict(u)
    tok = create_token(user_dict)
    return {"access_token": tok, "refresh_token": tok, "token_type": "bearer", "user": {k: v for k, v in user_dict.items() if k != "password_hash"}}

@router.get("/me")
async def me(u=Depends(get_current_user)):
    return {k:v for k,v in u.items() if k!="password_hash"}

@router.post("/logout")
async def logout(u=Depends(get_current_user)): return {"message":"Logout realizado"}

class RefreshReq(BaseModel):
    refresh_token:Optional[str]=None

@router.post("/refresh")
async def refresh(b: RefreshReq = RefreshReq(), creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    token = b.refresh_token or (creds.credentials if creds else None)
    if not token: raise HTTPException(401, "Token ausente")
    p = decode_token(token)
    u = (await db.execute(
        select(UserModel).where(or_(UserModel.email == p.get("email", "").lower(), UserModel.id == p.get("sub")))
    )).scalars().first()
    if not u: raise HTTPException(401, "Usuario nao encontrado")
    tok = create_token(model_to_dict(u))
    return {"access_token": tok, "refresh_token": tok, "token_type": "bearer"}

@router.get("/users")
async def get_auth_users(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(UserModel))).scalars().all()
    return [{k: v for k, v in model_to_dict(x).items() if k != "password_hash"} for x in users]

@router.post("/users")
async def create_user(b: CreateUserReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem criar novos acessos")
    if b.role not in ("GERENTE", "FUNCIONARIO"):
        raise HTTPException(400, "Cargo inválido. Use GERENTE ou FUNCIONARIO")

    email = b.email.strip().lower()
    existing = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Este e-mail já está cadastrado no sistema")

    user_count = (await db.execute(select(func.count()).select_from(UserModel))).scalar() or 0
    new_id = f"usr-{user_count + 1:03d}"
    pwd_hash = bcrypt.hashpw(b.password.encode(), bcrypt.gensalt()).decode()

    new_user = UserModel(
        id=new_id,
        company_id=u["company_id"],
        email=email,
        full_name=b.full_name,
        role=b.role,
        plan_scope="empresarial",
        password_hash=pwd_hash,
        is_active=True,
        mfa_enabled=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {k: v for k, v in model_to_dict(new_user).items() if k != "password_hash"}

@router.put("/users/{uid}")
async def upd_auth_user(uid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    usr = await db.get(UserModel, uid)
    if not usr: raise HTTPException(404)
    for k, v in d.items():
        if k in _USER_COLUMNS and k != "password_hash":
            setattr(usr, k, v.strip().lower() if k == "email" and isinstance(v, str) else v)
    await db.commit()
    await db.refresh(usr)
    return {k: v for k, v in model_to_dict(usr).items() if k != "password_hash"}
