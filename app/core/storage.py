# NOTA: Armazenamento privado de comprovantes e relatórios: em disco local ou em serviço compatível com S3.
#       Os arquivos nunca são públicos; só saem por rotas que conferem o dono.

"""Private file storage for attachments and exports (STO-1).

Two backends behind the same functions:
- local (default): files under STORAGE_DIR, as before;
- s3: any S3-compatible service (Supabase Storage, AWS S3, Cloudflare R2) via STORAGE_BACKEND=s3,
  S3_BUCKET, S3_ENDPOINT_URL, S3_REGION, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY — required as soon as
  more than one server instance runs.
Files are never public: they are served only by authenticated endpoints that check ownership.
"""

import asyncio
import os
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STORAGE_DIR = Path(os.getenv("STORAGE_DIR") or PROJECT_ROOT / "storage")

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".xml"}

_s3_client = None  # created lazily; tests may replace it


def backend() -> str:
    return os.getenv("STORAGE_BACKEND", "local").lower()


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client(
            "s3", endpoint_url=os.getenv("S3_ENDPOINT_URL") or None, region_name=os.getenv("S3_REGION") or None,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
        )
    return _s3_client


def _local_path(key: str) -> Path:
    target = (STORAGE_DIR / key).resolve()
    if STORAGE_DIR.resolve() not in target.parents:
        raise ValueError("chave de arquivo inválida")
    return target


async def put(key: str, content: bytes, content_type: str = "application/octet-stream") -> None:
    if backend() == "s3":
        await asyncio.to_thread(_s3().put_object, Bucket=os.environ["S3_BUCKET"], Key=key, Body=content, ContentType=content_type)
        return
    path = _local_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


async def get(key: str) -> bytes | None:
    if backend() == "s3":
        def _get():
            try:
                return _s3().get_object(Bucket=os.environ["S3_BUCKET"], Key=key)["Body"].read()
            except Exception:  # noqa: BLE001 - missing object or provider error: treated as not found
                return None
        return await asyncio.to_thread(_get)
    try:
        path = _local_path(key)
    except ValueError:
        return None
    return path.read_bytes() if path.exists() else None


async def delete(key: str) -> None:
    if backend() == "s3":
        await asyncio.to_thread(_s3().delete_object, Bucket=os.environ["S3_BUCKET"], Key=key)
        return
    try:
        _local_path(key).unlink(missing_ok=True)
    except ValueError:
        pass


async def delete_prefix(prefix: str) -> None:
    """Removes every file under a prefix (used when a company is erased)."""
    if backend() == "s3":
        def _purge():
            client, bucket = _s3(), os.environ["S3_BUCKET"]
            for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    client.delete_object(Bucket=bucket, Key=obj["Key"])
        await asyncio.to_thread(_purge)
        return
    folder = _local_path(prefix.rstrip("/"))
    if folder.exists():
        for f in folder.iterdir():
            f.unlink(missing_ok=True)
        folder.rmdir()


# ---------- attachments: key stored on the entry = "<company>/<uuid>.<ext>" ----------

def extension_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


async def save_attachment(company_id: str, filename: str, content: bytes) -> str:
    key = f"{company_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"
    await put(f"attachments/{key}", content)
    return key


async def read_attachment(key: str) -> bytes | None:
    return await get(f"attachments/{key}")


async def delete_attachment(key: str) -> None:
    await delete(f"attachments/{key}")


# ---------- exports ----------

async def save_export(company_id: str, filename: str, content: bytes, content_type: str) -> None:
    await put(f"exports/{company_id}/{filename}", content, content_type)


async def read_export(company_id: str, filename: str) -> bytes | None:
    return await get(f"exports/{company_id}/{filename}")


async def delete_company_files(company_id: str) -> None:
    await delete_prefix(f"attachments/{company_id}/")
    await delete_prefix(f"exports/{company_id}/")
