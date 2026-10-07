from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user, bearer, token_pair, user_from_token, create_mfa_token
from app.core import crypto
import json
import base64
import io
import pyotp
import qrcode
import qrcode.image.svg
from app.core import audit
from app.core.mailer import APP_URL, send_email
from app.core.legal import TERMS_VERSION
from app.core.notify import notify_user
import hashlib
import secrets
from app.core.passwords import validate_password, hash_password, check_password
from app.db.session import get_db
from app.db.models import UserModel, CompanyModel, PasswordResetModel
from app.db.utils import model_to_dict
from app.api.v1.endpoints.plans import PLANS_DB

router = APIRouter()

_USER_COLUMNS = {c.name for c in UserModel.__table__.columns}
_PRIVATE_USER_FIELDS = {"password_hash", "failed_login_count", "locked_until", "mfa_secret", "mfa_recovery_codes"}

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


def _public(user: dict) -> dict:
    return {k: v for k, v in user.items() if k not in _PRIVATE_USER_FIELDS}

class LoginReq(BaseModel):
    email:str; password:str; mfa_code:Optional[str]=None

class RegisterReq(BaseModel):
    full_name: str
    email: str
    password: str
    company_name: Optional[str] = "Minha Empresa"
    cnpj_cpf: Optional[str] = None
    selected_plan: Optional[str] = "plan-empresarial"
    accept_terms: bool = False

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

    if not b.accept_terms:
        raise HTTPException(400, "É preciso aceitar os Termos de Uso e a Política de Privacidade")
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
        mfa_enabled=False,
        terms_version=TERMS_VERSION,
        terms_accepted_at=datetime.utcnow().isoformat(),
    )
    db.add(new_user)
    await db.flush()  # company must exist before the audit row that references it (Postgres/MySQL enforce the FK)
    audit.record(db, "CADASTRO", company_id=company_id, user_id=user_id, entity="company", entity_id=company_id, details={"plano": b.selected_plan})
    await db.commit()
    await db.refresh(new_user)

    # company_name/selected_plan have no column on UserModel (schema gap, see task report) -
    # echoed back from the request so the response contract stays identical, not persisted.
    user_dict = model_to_dict(new_user)
    user_dict["company_name"] = b.company_name
    user_dict["selected_plan"] = b.selected_plan

    await send_email(email, "Bem-vindo ao TechConnect",
                     f"Olá, {b.full_name}! Sua conta da empresa {b.company_name or 'Minha Empresa'} foi criada.\n"
                     f"Acesse: {APP_URL}")
    return {**token_pair(user_dict), "user": _public(user_dict)}

@router.post("/login")
async def login(b: LoginReq, db: AsyncSession = Depends(get_db)):
    email = b.email.strip().lower()
    u = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if not u:
        raise HTTPException(401, "Credenciais invalidas")
    now = datetime.utcnow()
    if u.locked_until and datetime.fromisoformat(u.locked_until) > now:
        audit.record(db, "LOGIN_BLOQUEADO", company_id=u.company_id, user_id=u.id)
        await db.commit()
        raise HTTPException(429, f"Muitas tentativas incorretas. Tente novamente em até {LOCKOUT_MINUTES} minutos")
    if not check_password(b.password, u.password_hash):
        await _register_failure(db, u, "senha")
        raise HTTPException(401, "Credenciais invalidas")
    if u.is_active is False:
        raise HTTPException(401, "Usuario inativo")
    if u.mfa_enabled:
        if not b.mfa_code:
            return {"mfa_required": True, "mfa_token": create_mfa_token(model_to_dict(u))}
        if not await _verify_second_factor(db, u, b.mfa_code):
            await _register_failure(db, u, "codigo_2fa")
            raise HTTPException(401, "Código de verificação inválido")
    return await _complete_login(db, u)


async def _register_failure(db: AsyncSession, u: UserModel, step: str) -> None:
    """Wrong password or wrong 2FA code: both count toward the temporary lockout."""
    now = datetime.utcnow()
    u.failed_login_count = (u.failed_login_count or 0) + 1
    locked = u.failed_login_count >= MAX_FAILED_LOGINS
    if locked:
        u.locked_until = (now + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
        u.failed_login_count = 0
        await notify_user(db, u, "Sua conta foi bloqueada temporariamente",
                          f"Detectamos {MAX_FAILED_LOGINS} tentativas de login com senha ou código errados. O acesso fica bloqueado por "
                          f"{LOCKOUT_MINUTES} minutos. Se não foi você, redefina sua senha: {APP_URL}/esqueci-senha",
                          security=True)
    audit.record(db, "LOGIN_FALHA", company_id=u.company_id, user_id=u.id, details={"bloqueou": locked, "etapa": step})
    await db.commit()


async def _complete_login(db: AsyncSession, u: UserModel) -> dict:
    u.failed_login_count = 0
    u.locked_until = None
    audit.record(db, "LOGIN", company_id=u.company_id, user_id=u.id)
    await db.commit()
    user_dict = model_to_dict(u)
    return {**token_pair(user_dict), "user": _public(user_dict)}


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().replace("-", "").encode()).hexdigest()


async def _verify_second_factor(db: AsyncSession, u: UserModel, code: str) -> bool:
    """A current TOTP code (one step of clock drift tolerated) or an unused recovery code."""
    secret = crypto.decrypt(u.mfa_secret) if u.mfa_secret else None
    digits = code.strip().replace(" ", "")
    if secret and digits.isdigit() and pyotp.TOTP(secret).verify(digits, valid_window=1):
        return True
    hashes = json.loads(u.mfa_recovery_codes or "[]")
    if _hash_code(code) in hashes:
        hashes.remove(_hash_code(code))
        u.mfa_recovery_codes = json.dumps(hashes)
        audit.record(db, "CODIGO_RECUPERACAO_USADO", company_id=u.company_id, user_id=u.id, details={"restantes": len(hashes)})
        return True
    return False


class MfaLoginReq(BaseModel):
    mfa_token: str
    code: str


@router.post("/login/mfa")
async def login_mfa(b: MfaLoginReq, db: AsyncSession = Depends(get_db)):
    u = await user_from_token(b.mfa_token, "mfa", db)
    if u.locked_until and datetime.fromisoformat(u.locked_until) > datetime.utcnow():
        raise HTTPException(429, f"Muitas tentativas incorretas. Tente novamente em até {LOCKOUT_MINUTES} minutos")
    if not await _verify_second_factor(db, u, b.code):
        await _register_failure(db, u, "codigo_2fa")
        raise HTTPException(401, "Código de verificação inválido")
    return await _complete_login(db, u)

@router.get("/me")
async def me(u=Depends(get_current_user)):
    return _public(u)

@router.post("/logout")
async def logout(u=Depends(get_current_user)): return {"message":"Logout realizado"}

class RefreshReq(BaseModel):
    refresh_token:Optional[str]=None

@router.post("/refresh")
async def refresh(b: RefreshReq = RefreshReq(), creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    token = b.refresh_token or (creds.credentials if creds else None)
    if not token: raise HTTPException(401, "Token ausente")
    u = await user_from_token(token, "refresh", db)
    return token_pair(model_to_dict(u))

@router.get("/users")
async def get_auth_users(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem listar os acessos")
    users = (await db.execute(select(UserModel).where(UserModel.company_id == u["company_id"]))).scalars().all()
    return [_public(model_to_dict(x)) for x in users]

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
    audit.record_by(db, u, "USUARIO_CRIADO", entity="user", entity_id=new_id, details={"email": email, "cargo": b.role})
    await db.commit()
    await db.refresh(new_user)
    # The password is handed over by the admin, never by e-mail.
    await send_email(email, "Você recebeu acesso ao TechConnect",
                     f"Olá, {b.full_name}! {u['full_name']} criou um acesso para você. Entre em {APP_URL} com este e-mail "
                     f"e a senha combinada com o administrador, e troque-a em Minha Conta.")
    return _public(model_to_dict(new_user))

_UPD_USER_BLOCKED_COLUMNS = {"password_hash", "company_id", "id", "failed_login_count", "locked_until", "mfa_enabled", "mfa_secret", "mfa_recovery_codes"}

@router.put("/users/{uid}")
async def upd_auth_user(uid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem editar acessos")
    usr = await db.get(UserModel, uid)
    if not usr or usr.company_id != u["company_id"]:
        raise HTTPException(404)
    if "role" in d and d["role"] != usr.role and d["role"] not in ("ADMIN", "GERENTE", "FUNCIONARIO"):
        raise HTTPException(400, "Cargo inválido. Use ADMIN, GERENTE ou FUNCIONARIO")
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
    changes = {k: v for k, v in d.items() if k in _USER_COLUMNS and k not in _UPD_USER_BLOCKED_COLUMNS}
    audit.record_by(db, u, "USUARIO_ALTERADO", entity="user", entity_id=uid, details=changes)
    await db.commit()
    await db.refresh(usr)
    return _public(model_to_dict(usr))


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
    audit.record_by(db, u, "SENHA_ALTERADA", entity="user", entity_id=usr.id)
    await db.commit()
    await notify_user(db, usr, "Sua senha foi alterada", "A senha da sua conta TechConnect foi alterada agora. "
                      f"Se não foi você, redefina-a em {APP_URL}/esqueci-senha.", security=True)
    # Old tokens die with the old password; hand back a fresh pair so this session continues.
    return {"message": "Senha alterada", **token_pair(model_to_dict(usr))}


class ResetPasswordReq(BaseModel):
    new_password: str

@router.post("/users/{uid}/reset-password")
async def reset_user_password(uid: str, b: ResetPasswordReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Admin sets a temporary password; the person's open sessions end immediately."""
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem redefinir senhas")
    usr = await db.get(UserModel, uid)
    if not usr or usr.company_id != u["company_id"]:
        raise HTTPException(404)
    validate_password(b.new_password)
    usr.password_hash = hash_password(b.new_password)
    usr.failed_login_count = 0
    usr.locked_until = None
    audit.record_by(db, u, "SENHA_REDEFINIDA", entity="user", entity_id=uid)
    await db.commit()
    return {"message": "Senha redefinida"}


RESET_TTL_MINUTES = 60


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class ForgotPasswordReq(BaseModel):
    email: str


@router.post("/forgot-password")
async def forgot_password(b: ForgotPasswordReq, db: AsyncSession = Depends(get_db)):
    """Same answer whether or not the e-mail exists, so accounts cannot be discovered."""
    answer = {"message": "Se o e-mail estiver cadastrado, enviaremos um link para redefinir a senha."}
    usr = (await db.execute(select(UserModel).where(UserModel.email == b.email.strip().lower()))).scalar_one_or_none()
    if not usr or usr.is_active is False:
        return answer
    now = datetime.utcnow()
    for old in (await db.execute(select(PasswordResetModel).where(PasswordResetModel.user_id == usr.id, PasswordResetModel.used_at.is_(None)))).scalars().all():
        old.used_at = now.isoformat()  # a new link invalidates the previous ones
    token = secrets.token_urlsafe(32)
    db.add(PasswordResetModel(id=f"pwr-{uuid.uuid4().hex[:12]}", user_id=usr.id, token_hash=_hash_token(token),
                              expires_at=(now + timedelta(minutes=RESET_TTL_MINUTES)).isoformat()))
    audit.record(db, "SENHA_RECUPERACAO_SOLICITADA", company_id=usr.company_id, user_id=usr.id)
    await db.commit()
    await send_email(usr.email, "Redefinição de senha do TechConnect",
                     f"Recebemos um pedido para redefinir sua senha. O link vale por {RESET_TTL_MINUTES} minutos:\n"
                     f"{APP_URL}/redefinir-senha?token={token}\n\nSe não foi você, ignore este e-mail.")
    return answer


class ResetPasswordWithTokenReq(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
async def reset_password_with_token(b: ResetPasswordWithTokenReq, db: AsyncSession = Depends(get_db)):
    reset = (await db.execute(select(PasswordResetModel).where(PasswordResetModel.token_hash == _hash_token(b.token)))).scalar_one_or_none()
    now = datetime.utcnow()
    if not reset or reset.used_at or datetime.fromisoformat(reset.expires_at) < now:
        raise HTTPException(400, "Link inválido ou expirado. Peça um novo em \"Esqueci minha senha\"")
    validate_password(b.new_password)
    usr = await db.get(UserModel, reset.user_id)
    if not usr or usr.is_active is False:
        raise HTTPException(400, "Link inválido ou expirado")
    usr.password_hash = hash_password(b.new_password)
    usr.failed_login_count = 0
    usr.locked_until = None
    reset.used_at = now.isoformat()
    audit.record(db, "SENHA_REDEFINIDA_POR_EMAIL", company_id=usr.company_id, user_id=usr.id)
    await db.commit()
    await notify_user(db, usr, "Sua senha foi alterada", "A senha da sua conta TechConnect foi redefinida pelo link de recuperação. "
                      f"Se não foi você, fale com o administrador da sua empresa.", security=True)
    return {"message": "Senha redefinida. Entre com a nova senha."}


# ---------- two-factor authentication (AUTH-1) ----------

def _qr_svg_data_uri(uri: str) -> str:
    buf = io.BytesIO()
    qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage, box_size=8).save(buf)
    return "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()


@router.post("/mfa/setup")
async def mfa_setup(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Creates a new (not yet active) seed. It only takes effect after /mfa/enable confirms a code."""
    usr = await db.get(UserModel, u["id"])
    if usr.mfa_enabled:
        raise HTTPException(400, "A verificação em duas etapas já está ativa")
    secret = pyotp.random_base32()
    usr.mfa_secret = crypto.encrypt(secret)
    await db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=usr.email, issuer_name="TechConnect")
    return {"secret": secret, "otpauth_uri": uri, "qr_svg": _qr_svg_data_uri(uri)}


class MfaCodeReq(BaseModel):
    code: str


@router.post("/mfa/enable")
async def mfa_enable(b: MfaCodeReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    usr = await db.get(UserModel, u["id"])
    secret = crypto.decrypt(usr.mfa_secret) if usr.mfa_secret else None
    if usr.mfa_enabled or not secret:
        raise HTTPException(400, "Inicie a configuração antes de confirmar")
    if not pyotp.TOTP(secret).verify(b.code.strip(), valid_window=1):
        raise HTTPException(400, "Código inválido. Confira o horário do celular e tente de novo")
    codes = [f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}" for _ in range(8)]
    usr.mfa_recovery_codes = json.dumps([_hash_code(c) for c in codes])
    usr.mfa_enabled = True
    audit.record_by(db, u, "2FA_ATIVADO", entity="user", entity_id=usr.id)
    await db.commit()
    await notify_user(db, usr, "Verificação em duas etapas ativada",
                      "A verificação em duas etapas foi ativada na sua conta TechConnect.", security=True)
    return {"recovery_codes": codes}


class MfaDisableReq(BaseModel):
    password: str
    code: str


@router.post("/mfa/disable")
async def mfa_disable(b: MfaDisableReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    usr = await db.get(UserModel, u["id"])
    if not check_password(b.password, usr.password_hash):
        raise HTTPException(400, "Senha incorreta")
    if not usr.mfa_enabled or not await _verify_second_factor(db, usr, b.code):
        raise HTTPException(400, "Código inválido")
    _clear_mfa(usr)
    audit.record_by(db, u, "2FA_DESATIVADO", entity="user", entity_id=usr.id)
    await db.commit()
    await notify_user(db, usr, "Verificação em duas etapas desativada",
                      "A verificação em duas etapas foi desativada na sua conta TechConnect. Se não foi você, troque sua senha.", security=True)
    return {"message": "Verificação em duas etapas desativada"}


def _clear_mfa(usr: UserModel) -> None:
    usr.mfa_enabled = False
    usr.mfa_secret = None
    usr.mfa_recovery_codes = None


@router.post("/users/{uid}/mfa/disable")
async def admin_disable_mfa(uid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """For a member who lost the phone and the recovery codes."""
    if u["role"] != "ADMIN":
        raise HTTPException(403, "Somente administradores podem desativar a verificação de outra pessoa")
    usr = await db.get(UserModel, uid)
    if not usr or usr.company_id != u["company_id"]:
        raise HTTPException(404)
    _clear_mfa(usr)
    audit.record_by(db, u, "2FA_DESATIVADO_PELO_ADMIN", entity="user", entity_id=uid)
    await db.commit()
    await notify_user(db, usr, "Verificação em duas etapas desativada",
                      f"{u['full_name']} desativou a verificação em duas etapas da sua conta. Ative de novo em Minha Conta.", security=True)
    return {"message": "Verificação em duas etapas desativada"}


class AcceptTermsReq(BaseModel):
    version: str


@router.post("/accept-terms")
async def accept_terms(b: AcceptTermsReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """People created by an admin (and accounts older than the current texts) accept on their next access."""
    if b.version != TERMS_VERSION:
        raise HTTPException(400, "Versão dos termos desatualizada; recarregue a página")
    usr = await db.get(UserModel, u["id"])
    usr.terms_version = TERMS_VERSION
    usr.terms_accepted_at = datetime.utcnow().isoformat()
    audit.record_by(db, u, "TERMOS_ACEITOS", entity="user", entity_id=usr.id, details={"versao": TERMS_VERSION})
    await db.commit()
    return {"terms_version": usr.terms_version, "terms_accepted_at": usr.terms_accepted_at}
