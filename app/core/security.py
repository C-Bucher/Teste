from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
from app.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXP
from app.db.database import USERS_DB

bearer = HTTPBearer(auto_error=False)

def create_token(user):
    payload={"sub":user["id"],"email":user["email"],"role":user["role"],"exp":datetime.utcnow()+timedelta(minutes=TOKEN_EXP)}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def decode_token(token):
    try: return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except: raise HTTPException(status_code=401,detail="Token invalido")

def get_current_user(creds:HTTPAuthorizationCredentials=Depends(bearer)):
    if not creds: raise HTTPException(401,"Token ausente")
    p=decode_token(creds.credentials)
    u=USERS_DB.get(p.get("email")) or next((v for v in USERS_DB.values() if v["id"]==p.get("sub")),None)
    if not u: raise HTTPException(401,"Usuario nao encontrado")
    return u
