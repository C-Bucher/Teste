# NOTA: Regras e criptografia de senha: mínimo de 8 caracteres com letras e números, hash bcrypt e verificação.

import os
import re

import bcrypt
from fastapi import HTTPException

# Production keeps bcrypt's default cost; the test suite lowers it to stay fast.
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

PASSWORD_RULE = "A senha deve ter pelo menos 8 caracteres, com letras e números"


def validate_password(password: str) -> None:
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(400, PASSWORD_RULE)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())
