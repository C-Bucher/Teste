import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-secret-change-in-production")
ALGORITHM  = "HS256"
TOKEN_EXP  = 480
