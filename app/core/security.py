import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXP, REFRESH_TOKEN_EXP_DAYS
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import UserModel
from app.db.utils import model_to_dict

bearer = HTTPBearer(auto_error=False)


def _password_fingerprint(password_hash: str) -> str:
    # Changes whenever the password changes, which revokes every token issued before it.
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def _encode(user: dict, kind: str, expires: timedelta) -> str:
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "type": kind,
        "pwd": _password_fingerprint(user["password_hash"]),
        "exp": datetime.utcnow() + expires,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_token(user: dict) -> str:
    return _encode(user, "access", timedelta(minutes=TOKEN_EXP))


def create_refresh_token(user: dict) -> str:
    return _encode(user, "refresh", timedelta(days=REFRESH_TOKEN_EXP_DAYS))


def create_mfa_token(user: dict) -> str:
    """Proves the password step only; accepted solely by /auth/login/mfa."""
    return _encode(user, "mfa", timedelta(minutes=5))


def token_pair(user: dict) -> dict:
    return {"access_token": create_token(user), "refresh_token": create_refresh_token(user), "token_type": "bearer"}


def decode_token(token):
    try: return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except Exception: raise HTTPException(status_code=401,detail="Token invalido")


async def user_from_token(token: str, kind: str, db: AsyncSession) -> UserModel:
    p = decode_token(token)
    if p.get("type") != kind:
        raise HTTPException(401, "Token invalido")
    u = await db.get(UserModel, p.get("sub"))
    if not u: raise HTTPException(401,"Usuario nao encontrado")
    if u.is_active is False: raise HTTPException(401,"Usuario inativo")
    if p.get("pwd") != _password_fingerprint(u.password_hash):
        raise HTTPException(401, "Sessao expirada, faca login novamente")
    return u


async def get_current_user(creds:HTTPAuthorizationCredentials=Depends(bearer), db: AsyncSession = Depends(get_db)):
    if not creds: raise HTTPException(401,"Token ausente")
    return model_to_dict(await user_from_token(creds.credentials, "access", db))
