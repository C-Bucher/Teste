"""In-app notification for the company, plus an e-mail to each person who keeps e-mail alerts on (NOT-1)."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mailer import send_email
from app.db.models import NotificationModel, NotificationPreferenceModel, UserModel


async def _wants_email(db: AsyncSession, user_id: str) -> bool:
    prefs = await db.get(NotificationPreferenceModel, user_id)
    return prefs is None or prefs.email_enabled is not False


async def notify_company(db: AsyncSession, company_id: str, title: str, message: str, *,
                         kind: str = "INFO", admins_only: bool = True) -> None:
    """Adds the notification to the session (caller commits) and e-mails the company's admins."""
    db.add(NotificationModel(id=f"ntf-{uuid.uuid4().hex[:12]}", company_id=company_id, title=title[:255],
                             message=message[:255], type=kind, is_read=False, is_archived=False,
                             created_at=datetime.utcnow().isoformat()))
    q = select(UserModel).where(UserModel.company_id == company_id, UserModel.is_active == True)  # noqa: E712
    if admins_only:
        q = q.where(UserModel.role == "ADMIN")
    for user in (await db.execute(q)).scalars().all():
        if await _wants_email(db, user.id):
            await send_email(user.email, title, message)


async def notify_user(db: AsyncSession, user: UserModel, subject: str, text: str, *, security: bool = False) -> None:
    """Security e-mails (password changed, account locked) ignore the preference on purpose."""
    if security or await _wants_email(db, user.id):
        await send_email(user.email, subject, text)
