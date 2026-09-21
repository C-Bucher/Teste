from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
from app.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXP
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import UserModel
from app.db.utils import model_to_dict

bearer = HTTPBearer(auto_error=False)

def create_token(user):
    payload={"sub":user["id"],"email":user["email"],"role":user["role"],"exp":datetime.utcnow()+timedelta(minutes=TOKEN_EXP)}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def decode_token(token):
    try: return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except: raise HTTPException(status_code=401,detail="Token invalido")

async def get_current_user(creds:HTTPAuthorizationCredentials=Depends(bearer), db: AsyncSession = Depends(get_db)):
    if not creds: raise HTTPException(401,"Token ausente")
    p=decode_token(creds.credentials)
    result = await db.execute(select(UserModel).where(or_(UserModel.email == p.get("email", "").lower(), UserModel.id == p.get("sub"))))
    u = result.scalars().first()
    if not u: raise HTTPException(401,"Usuario nao encontrado")
    if u.is_active is False: raise HTTPException(401,"Usuario inativo")
    return model_to_dict(u)
