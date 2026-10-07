"""Symmetric encryption for secrets stored in the database (e.g. the TOTP seed).

Keyed by ENCRYPTION_KEY, falling back to SECRET_KEY. Keep ENCRYPTION_KEY stable: rotating the JWT
SECRET_KEY must not wipe everyone's two-factor setup."""

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import SECRET_KEY

_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(f"techconnect:{os.getenv('ENCRYPTION_KEY') or SECRET_KEY}".encode()).digest()))


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt(token: str) -> str | None:
    """None when the value was encrypted with another SECRET_KEY (e.g. after a key rotation)."""
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None
