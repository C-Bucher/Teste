from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.core.security import create_token, decode_token, get_current_user, bearer
from app.core.passwords import validate_password, hash_password, check_password
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

    validate_password(b.password)
    plan = next((p for p in PLANS_DB if p["id"] == b.selected_plan), None)
    if not plan:
        raise HTTPException(400, "Plano inválido")
    company_id = f"cmp-{uuid.uuid4().hex[:12]}"
    db.add(CompanyModel(id=company_id, name=b.company_name or "Minha Empresa", cnpj=b.cnpj_cpf))

    user_id = f"usr-{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(b.password)

    plan_scope = plan["scope"]

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
    if not u or not check_password(b.password, u.password_hash):
        raise HTTPException(401, "Credenciais invalidas")
    if u.is_active is False:
        raise HTTPException(401, "Usuario inativo")
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
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem listar os acessos")
    users = (await db.execute(select(UserModel).where(UserModel.company_id == u["company_id"]))).scalars().all()
    return [{k: v for k, v in model_to_dict(x).items() if k != "password_hash"} for x in users]

@router.post("/users")
async def create_user(b: CreateUserReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem criar novos acessos")
    if b.role not in ("GERENTE", "FUNCIONARIO"):
        raise HTTPException(400, "Cargo inválido. Use GERENTE ou FUNCIONARIO")
    validate_password(b.password)

    email = b.email.strip().lower()
    existing = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Este e-mail já está cadastrado no sistema")

    new_id = f"usr-{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(b.password)

    new_user = UserModel(
        id=new_id,
        company_id=u["company_id"],
        email=email,
        full_name=b.full_name,
        role=b.role,
        plan_scope=u.get("plan_scope", "empresarial"),
        password_hash=pwd_hash,
        is_active=True,
        mfa_enabled=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {k: v for k, v in model_to_dict(new_user).items() if k != "password_hash"}

_UPD_USER_BLOCKED_COLUMNS = {"password_hash", "company_id", "id"}

@router.put("/users/{uid}")
async def upd_auth_user(uid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem editar acessos")
    usr = await db.get(UserModel, uid)
    if not usr or usr.company_id != u["company_id"]:
        raise HTTPException(404)
    if "role" in d and d["role"] != usr.role and d["role"] not in ("GERENTE", "FUNCIONARIO"):
        raise HTTPException(400, "Cargo inválido. Use GERENTE ou FUNCIONARIO")
    if usr.id == u["id"] and (d.get("is_active") is False or d.get("role") not in (None, "ADMIN")):
        raise HTTPException(400, "O administrador não pode remover o próprio acesso administrativo")
    removing_admin = usr.role == "ADMIN" and (d.get("is_active") is False or d.get("role") not in (None, "ADMIN"))
    if removing_admin:
        admin_count = (await db.execute(
            select(func.count()).select_from(UserModel).where(
                UserModel.company_id == u["company_id"],
                UserModel.role == "ADMIN",
                UserModel.is_active == True,
            )
        )).scalar() or 0
        if admin_count <= 1:
            raise HTTPException(400, "A empresa deve manter pelo menos um administrador ativo")
    if "email" in d:
        normalized_email = str(d["email"]).strip().lower()
        duplicate = (await db.execute(select(UserModel).where(UserModel.email == normalized_email, UserModel.id != uid))).scalar_one_or_none()
        if duplicate:
            raise HTTPException(400, "Este e-mail já está cadastrado no sistema")
    for k, v in d.items():
        if k in _USER_COLUMNS and k not in _UPD_USER_BLOCKED_COLUMNS:
            setattr(usr, k, v.strip().lower() if k == "email" and isinstance(v, str) else v)
    await db.commit()
    await db.refresh(usr)
    return {k: v for k, v in model_to_dict(usr).items() if k != "password_hash"}


class ChangePasswordReq(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
async def change_password(b: ChangePasswordReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    usr = await db.get(UserModel, u["id"])
    if not check_password(b.current_password, usr.password_hash):
        raise HTTPException(400, "Senha atual incorreta")
    validate_password(b.new_password)
    usr.password_hash = hash_password(b.new_password)
    await db.commit()
    return {"message": "Senha alterada"}
