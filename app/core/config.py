import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-secret-change-in-production")
ALGORITHM  = "HS256"
TOKEN_EXP  = 480
APP_ENV = os.getenv("APP_ENV", "development").lower()
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]

if APP_ENV == "production" and SECRET_KEY == "insecure-dev-secret-change-in-production":
    raise RuntimeError("SECRET_KEY deve ser configurada em produção")
