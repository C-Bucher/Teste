import logging
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").lower()

SECRET_KEY = os.getenv("SECRET_KEY") or ""
if not SECRET_KEY:
    if APP_ENV == "production":
        raise RuntimeError("SECRET_KEY deve ser configurada em produção")
    # No publicly known fallback: an ephemeral key means tokens stop working on restart, which is fine for dev.
    SECRET_KEY = secrets.token_hex(32)
    logging.getLogger("techconnect").warning("SECRET_KEY ausente: usando chave temporária (tokens expiram ao reiniciar)")

ALGORITHM  = "HS256"
TOKEN_EXP  = 60            # access token, minutes
REFRESH_TOKEN_EXP_DAYS = 7
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
