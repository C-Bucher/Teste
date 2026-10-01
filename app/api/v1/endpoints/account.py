"""The signed-in user's own account: LGPD data export and account deletion."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit, storage
from app.core.passwords import check_password
from app.core.security import get_current_user
from app.db import models as m
from app.db.session import get_db
from app.db.utils import models_to_dicts

router = APIRouter()

# Order matters for deletion: bank transactions before the bank accounts they belong to.
PERSONAL_MODELS = [
    m.BankTransactionModel, m.CategorizationRuleModel, m.BankAccountModel,
    m.PersonalAccountModel, m.PersonalBudgetModel, m.PersonalCategoryModel, m.PersonalDebtModel,
    m.PersonalEntryModel, m.PersonalGoalModel, m.PersonalOkrModel, m.PersonalSplitModel,
    m.PersonalSubscriptionModel, m.PersonalTimeboxModel,
]
_PRIVATE_USER_FIELDS = {"password_hash", "failed_login_count", "locked_until"}


@router.get("/export")
async def export_my_data(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Right of access (LGPD art. 18): everything stored about the signed-in person."""
    personal = {}
    for model in PERSONAL_MODELS:
        rows = (await db.execute(select(model).where(model.owner_id == u["id"]))).scalars().all()
        personal[model.__tablename__] = models_to_dicts(rows)
    activity = (await db.execute(
        select(m.AuditLogModel).where(m.AuditLogModel.user_id == u["id"]).order_by(m.AuditLogModel.created_at)
    )).scalars().all()
    audit.record_by(db, u, "DADOS_EXPORTADOS", entity="user", entity_id=u["id"])
    await db.commit()
    return {
        "perfil": {k: v for k, v in u.items() if k not in _PRIVATE_USER_FIELDS},
        "dados_pessoais": personal,
        "registro_de_atividades": models_to_dicts(activity),
    }


class DeleteAccountReq(BaseModel):
    password: str


async def _purge_company(db: AsyncSession, company_id: str) -> None:
    """Deletes every business row of a company, children before parents."""
    # IDs are materialised first: MySQL rejects DELETE ... WHERE id IN (SELECT ... FROM the same table).
    async def ids(stmt) -> list[str]:
        return list((await db.execute(stmt)).scalars().all())

    project_ids = await ids(select(m.ProjectModel.id).where(m.ProjectModel.company_id == company_id))
    column_ids = await ids(select(m.KanbanColumnModel.id).where(m.KanbanColumnModel.project_id.in_(project_ids)))
    card_ids = await ids(select(m.KanbanCardModel.id).where(m.KanbanCardModel.column_id.in_(column_ids)))
    employee_ids = await ids(select(m.EmployeeModel.id).where(m.EmployeeModel.company_id == company_id))
    subscription_ids = await ids(select(m.SubscriptionModel.id).where(m.SubscriptionModel.company_id == company_id))

    await db.execute(delete(m.CardCommentModel).where(m.CardCommentModel.card_id.in_(card_ids)))
    await db.execute(delete(m.ActiveTimerModel).where(m.ActiveTimerModel.card_id.in_(card_ids)))
    await db.execute(delete(m.KanbanCardModel).where(m.KanbanCardModel.id.in_(card_ids)))
    await db.execute(delete(m.KanbanColumnModel).where(m.KanbanColumnModel.id.in_(column_ids)))
    await db.execute(delete(m.SalaryHistoryModel).where(m.SalaryHistoryModel.employee_id.in_(employee_ids)))
    await db.execute(delete(m.InvoiceModel).where(m.InvoiceModel.subscription_id.in_(subscription_ids)))
    # Every table scoped by company_id, children before parents; new tables are covered automatically.
    for table in reversed(m.Base.metadata.sorted_tables):
        if "company_id" in table.c and table.name not in ("users", "companies"):
            await db.execute(delete(table).where(table.c.company_id == company_id))
    for folder in (storage.ATTACHMENTS_DIR / company_id, storage.EXPORTS_DIR / company_id):
        if folder.exists():
            for f in folder.iterdir():
                f.unlink(missing_ok=True)
            folder.rmdir()


@router.delete("")
async def delete_my_account(b: DeleteAccountReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Right to erasure (LGPD art. 18). A sole user takes the whole company with them;
    otherwise only the person's own data goes, and the team keeps the company."""
    user = await db.get(m.UserModel, u["id"])
    if not check_password(b.password, user.password_hash):
        raise HTTPException(400, "Senha incorreta")
    company_id = user.company_id
    others = (await db.execute(
        select(func.count()).select_from(m.UserModel).where(m.UserModel.company_id == company_id, m.UserModel.id != user.id)
    )).scalar() or 0
    if others and user.role == "ADMIN":
        other_admins = (await db.execute(
            select(func.count()).select_from(m.UserModel).where(
                m.UserModel.company_id == company_id, m.UserModel.id != user.id,
                m.UserModel.role == "ADMIN", m.UserModel.is_active == True,  # noqa: E712
            )
        )).scalar() or 0
        if not other_admins:
            raise HTTPException(400, "Você é o único administrador. Promova outra pessoa a administrador antes de excluir sua conta")

    for model in PERSONAL_MODELS:
        await db.execute(delete(model).where(model.owner_id == user.id))
    await db.execute(delete(m.NotificationPreferenceModel).where(m.NotificationPreferenceModel.user_id == user.id))

    if others:
        audit.record(db, "CONTA_EXCLUIDA", company_id=company_id, user_id=user.id, entity="user", entity_id=user.id)
        await db.delete(user)
    else:
        await _purge_company(db, company_id)
        await db.delete(user)
        await db.flush()
        company = await db.get(m.CompanyModel, company_id)
        if company:
            await db.delete(company)
    await db.commit()
    return {"message": "Conta excluída"}
