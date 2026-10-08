"""Audit trail (SEC-2). `record` only adds the row to the session: it is committed together with the change it describes."""

import json
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLogModel

client_ip: ContextVar[Optional[str]] = ContextVar("client_ip", default=None)


def record(
    db: AsyncSession,
    action: str,
    *,
    company_id: Optional[str],
    user_id: Optional[str],
    entity: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> None:
    db.add(AuditLogModel(
        id=f"aud-{uuid.uuid4().hex}",
        company_id=company_id,
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
        ip=client_ip.get(),
        created_at=datetime.utcnow().isoformat(),
    ))


def record_by(db: AsyncSession, u: dict, action: str, **kwargs) -> None:
    """Shortcut for an action performed by the authenticated user `u`."""
    record(db, action, company_id=u.get("company_id"), user_id=u.get("id"), **kwargs)
