"""Private file storage for attachments. Files live outside the public /uploads mount
and are only served through authenticated endpoints that check ownership."""

import os
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENTS_DIR = Path(os.getenv("ATTACHMENTS_DIR") or PROJECT_ROOT / "storage" / "attachments")

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".xml"}


def extension_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def save(company_id: str, filename: str, content: bytes) -> str:
    """Stores the bytes and returns an opaque key (company folder + random name)."""
    key = f"{company_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"
    target = ATTACHMENTS_DIR / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return key


def path_for(key: str) -> Path:
    target = (ATTACHMENTS_DIR / key).resolve()
    if ATTACHMENTS_DIR.resolve() not in target.parents:
        raise ValueError("chave de anexo inválida")
    return target


def delete(key: str) -> None:
    try:
        path_for(key).unlink(missing_ok=True)
    except ValueError:
        pass
