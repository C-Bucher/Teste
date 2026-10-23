# NOTA: Regras de acesso por assinatura: define quem pode usar o produto (teste de 7 dias, ativo, em atraso com 5 dias de tolerância, cancelado).
#       Bloqueia com erro 402 quando não há acesso.

"""Who may use the product: trial, paid period, grace after an overdue charge, cancellation (PAY-1).

A company is allowed in when ANY of its live subscriptions grants access:
- TRIAL     until trial_ends_at
- ACTIVE    until current_period_end + GRACE_DAYS (renewals extend it via the provider webhook)
- PAST_DUE  until the oldest overdue charge is GRACE_DAYS old
- CANCELED  until current_period_end (already paid for)
PENDING (a checkout waiting for its first payment) grants nothing on its own.
"""

import os
import uuid
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.plans import PLANS_DB
from app.core.security import get_current_user
from app.db.models import InvoiceModel, PlanModel, SubscriptionModel, UserModel
from app.db.session import get_db

TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "7"))
GRACE_DAYS = int(os.getenv("GRACE_DAYS", "5"))
CYCLE_DAYS = {"monthly": 30, "yearly": 365}
_PLAN_BY_SCOPE = {"pessoal": "plan-pessoal", "empresarial": "plan-empresarial", "completo": "plan-completo"}
LIVE_STATUSES = ("TRIAL", "PENDING", "ACTIVE", "PAST_DUE", "CANCELED")


def plan_by_id(plan_id: str) -> dict:
    return next(p for p in PLANS_DB if p["id"] == plan_id)


async def ensure_plan_row(db: AsyncSession, plan_data: dict) -> PlanModel:
    """Upserts the catalog entry so a stored row never keeps an outdated price."""
    plan = await db.get(PlanModel, plan_data["id"])
    if plan is None:
        plan = PlanModel(id=plan_data["id"])
        db.add(plan)
    limits = plan_data.get("limits", {})
    plan.name = plan_data["name"]
    plan.tagline = plan_data.get("tagline")
    plan.price_monthly = plan_data["price_monthly"]
    plan.price_yearly = plan_data["price_yearly"]
    plan.max_employees = limits.get("max_employees", 0)
    plan.max_projects = limits.get("max_projects", 0)
    plan.ai_cfo_unlimited = limits.get("ai_queries") == -1
    await db.flush()
    return plan


async def start_trial(db: AsyncSession, company_id: str, plan_id: str) -> SubscriptionModel:
    plan = plan_by_id(plan_id)
    await ensure_plan_row(db, plan)
    now = datetime.utcnow()
    sub = SubscriptionModel(
        id=f"sub-{uuid.uuid4().hex[:10]}", company_id=company_id, plan_id=plan_id, billing_cycle="monthly",
        amount=plan["price_monthly"], status="TRIAL", payment_method=None, auto_renew=False, provider=None,
        trial_ends_at=(now + timedelta(days=TRIAL_DAYS)).isoformat(), current_period_end=(now + timedelta(days=TRIAL_DAYS)).isoformat(),
    )
    db.add(sub)
    await db.flush()
    return sub


async def _oldest_overdue_due_date(db: AsyncSession, sub_id: str) -> str | None:
    return (await db.execute(
        select(InvoiceModel.due_date).where(InvoiceModel.subscription_id == sub_id, InvoiceModel.status == "OVERDUE")
        .order_by(InvoiceModel.due_date).limit(1)
    )).scalar_one_or_none()


async def grants_access(db: AsyncSession, sub: SubscriptionModel, now: datetime) -> bool:
    grace = timedelta(days=GRACE_DAYS)
    if sub.status == "TRIAL":
        return bool(sub.trial_ends_at) and datetime.fromisoformat(sub.trial_ends_at) > now
    if sub.status == "ACTIVE":
        return datetime.fromisoformat(sub.current_period_end) + grace > now
    if sub.status == "PAST_DUE":
        due = await _oldest_overdue_due_date(db, sub.id)
        return due is None or datetime.fromisoformat(due) + grace > now
    if sub.status == "CANCELED":
        return datetime.fromisoformat(sub.current_period_end) > now
    return False


async def live_subscriptions(db: AsyncSession, company_id: str) -> list[SubscriptionModel]:
    return list((await db.execute(
        select(SubscriptionModel).where(SubscriptionModel.company_id == company_id, SubscriptionModel.status.in_(LIVE_STATUSES))
        .order_by(SubscriptionModel.created_at.desc())
    )).scalars().all())


async def access_state(db: AsyncSession, u: dict) -> dict:
    """{allowed, subscription}; a company that predates billing gets a trial instead of a lockout."""
    subs = await live_subscriptions(db, u["company_id"])
    if not subs:
        scope_plan = _PLAN_BY_SCOPE.get(u.get("plan_scope") or "", "plan-empresarial")
        subs = [await start_trial(db, u["company_id"], scope_plan)]
        await db.commit()
    now = datetime.utcnow()
    for sub in subs:
        if await grants_access(db, sub, now):
            return {"allowed": True, "subscription": sub}
    return {"allowed": False, "subscription": subs[0]}


async def require_active_subscription(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    state = await access_state(db, u)
    if not state["allowed"]:
        raise HTTPException(402, "Sua assinatura está inativa. Regularize o pagamento em Assinatura para voltar a usar o sistema.",
                            headers={"X-Subscription": "blocked"})
    return u


async def apply_plan_scope(db: AsyncSession, company_id: str, plan_id: str) -> None:
    scope = plan_by_id(plan_id)["scope"]
    for user in (await db.execute(select(UserModel).where(UserModel.company_id == company_id))).scalars().all():
        user.plan_scope = scope
