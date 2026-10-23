# NOTA: Descobre o plano atual da empresa e calcula o quanto dos limites já foi usado (ex.: conexões bancárias).

"""The plan a company is on, and how much of its limits it uses (LIM-1)."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.plans import PLANS_DB
from app.db.models import BankAccountModel, SubscriptionModel, UserModel

_PLAN_BY_SCOPE = {"pessoal": "plan-pessoal", "empresarial": "plan-empresarial", "completo": "plan-completo"}


async def current_plan(db: AsyncSession, u: dict) -> dict:
    """Active subscription first; a company that never checked out falls back to its scope's base plan."""
    plan_id = (await db.execute(
        select(SubscriptionModel.plan_id).where(
            SubscriptionModel.company_id == u["company_id"], SubscriptionModel.status == "ACTIVE",
        ).order_by(SubscriptionModel.created_at.desc()).limit(1)
    )).scalar_one_or_none() if u.get("company_id") else None
    plan_id = plan_id or _PLAN_BY_SCOPE.get(u.get("plan_scope") or "", "plan-pessoal")
    return next(p for p in PLANS_DB if p["id"] == plan_id)


async def bank_connections_used(db: AsyncSession, u: dict) -> int:
    """Aggregator-linked accounts of the whole subscription: the company's and its people's personal ones."""
    company_users = select(UserModel.id).where(UserModel.company_id == u["company_id"])
    return (await db.execute(
        select(func.count()).select_from(BankAccountModel).where(
            BankAccountModel.source == "agregador",
            or_(BankAccountModel.company_id == u["company_id"], BankAccountModel.owner_id.in_(company_users)),
        )
    )).scalar() or 0
