import json
from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.integrations.ai import rules
from app.integrations.ai import service as ai_service
from app.integrations.ai.context import personal_snapshot
from app.integrations.ai.llm import Llm, LlmUnavailable, get_llm, parse_json
from app.db.session import get_db
from app.db.models import (
    PersonalEntryModel,
    PersonalCategoryModel,
    PersonalAccountModel,
    PersonalBudgetModel,
    PersonalGoalModel,
    PersonalDebtModel,
    PersonalSubscriptionModel,
    PersonalSplitModel,
    PersonalTimeboxModel,
    PersonalOkrModel,
)
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_ENTRY_COLUMNS = {c.name for c in PersonalEntryModel.__table__.columns}
async def _create_entry(d: dict, owner_id: str, db: AsyncSession):
    kwargs = {k: v for k, v in d.items() if k in _ENTRY_COLUMNS}
    kwargs["id"] = f"pes-{uuid.uuid4().hex[:6]}"
    kwargs.setdefault("date", date.today().isoformat())
    kwargs["owner_id"] = owner_id
    entry = PersonalEntryModel(**kwargs)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return model_to_dict(entry)


async def _delete_entry(eid: str, owner_id: str, db: AsyncSession):
    entry = await db.get(PersonalEntryModel, eid)
    if not entry or entry.owner_id != owner_id:
        raise HTTPException(404)
    await db.delete(entry)
    await db.commit()
    return {"success": True}


def _cols(model) -> set:
    return {c.name for c in model.__table__.columns}


_ACCOUNT_COLUMNS = _cols(PersonalAccountModel)
_BUDGET_COLUMNS = _cols(PersonalBudgetModel)
_GOAL_COLUMNS = _cols(PersonalGoalModel)
_DEBT_COLUMNS = _cols(PersonalDebtModel)
_SUBSCRIPTION_COLUMNS = _cols(PersonalSubscriptionModel)
_SPLIT_COLUMNS = _cols(PersonalSplitModel)
_TIMEBOX_COLUMNS = _cols(PersonalTimeboxModel)
_OKR_COLUMNS = _cols(PersonalOkrModel)


async def _list_owned(model, owner_id: str, db: AsyncSession):
    result = await db.execute(select(model).where(model.owner_id == owner_id))
    return models_to_dicts(result.scalars().all())


async def _create_owned(model, columns: set, prefix: str, d: dict, owner_id: str, db: AsyncSession, defaults: Optional[dict] = None):
    kwargs = {k: v for k, v in d.items() if k in columns}
    if defaults:
        for k, v in defaults.items():
            kwargs.setdefault(k, v)
    kwargs["id"] = f"{prefix}-{uuid.uuid4().hex[:6]}"
    kwargs["owner_id"] = owner_id
    obj = model(**kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return model_to_dict(obj)


async def _delete_owned(model, oid: str, owner_id: str, db: AsyncSession):
    obj = await db.get(model, oid)
    if not obj or obj.owner_id != owner_id:
        raise HTTPException(404)
    await db.delete(obj)
    await db.commit()
    return {"success": True}


async def _ensure_personal_categories(owner_id: str, db: AsyncSession) -> None:
    existing = await db.execute(select(PersonalCategoryModel.id).where(PersonalCategoryModel.owner_id == owner_id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return
    defaults = [("Salário", "RECEITA"), ("Moradia", "DESPESA"), ("Alimentação", "DESPESA"), ("Saúde", "DESPESA")]
    for name, category_type in defaults:
        db.add(PersonalCategoryModel(id=f"pc-{uuid.uuid4().hex[:8]}", owner_id=owner_id, name=name, type=category_type))
    await db.commit()


@router.get("/transactions")
async def get_pers_tx(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonalEntryModel).where(PersonalEntryModel.owner_id == u["id"]))
    return models_to_dicts(result.scalars().all())
@router.post("/transactions")
async def create_pers_tx(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_entry(d, u["id"], db)
@router.delete("/transactions/{eid}")
async def del_pers_tx(eid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_entry(eid, u["id"], db)

@router.get("/categories")
async def get_pers_cats(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _ensure_personal_categories(u["id"], db)
    result = await db.execute(select(PersonalCategoryModel).where(PersonalCategoryModel.owner_id == u["id"]))
    return models_to_dicts(result.scalars().all())

@router.get("/timeboxes")
async def get_timeboxes(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalTimeboxModel, u["id"], db)
@router.post("/timeboxes")
async def create_timebox(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalTimeboxModel, _TIMEBOX_COLUMNS, "ptb", d, u["id"], db)

@router.get("/okrs")
async def get_okrs(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalOkrModel, u["id"], db)
@router.post("/okrs")
async def create_okr(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalOkrModel, _OKR_COLUMNS, "pokr", d, u["id"], db)

@router.get("/dashboard")
async def pers_dash(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonalEntryModel).where(PersonalEntryModel.owner_id == u["id"]))
    entries = models_to_dicts(result.scalars().all())
    rec=sum(e["amount"] for e in entries if e["type"]=="RECEITA")
    desp=sum(e["amount"] for e in entries if e["type"]=="DESPESA")
    return {"saldo":round(rec-desp,2),"balance":round(rec-desp,2),"receitas_mes":rec,"total_income":rec,"despesas_mes":desp,"total_expense":desp,"recent_entries":entries}

@router.get("/entries")
async def get_pers(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonalEntryModel).where(PersonalEntryModel.owner_id == u["id"]))
    items = models_to_dicts(result.scalars().all())
    return {"items":items,"total":len(items)}
@router.post("/entries")
async def create_pers(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_entry(d, u["id"], db)
@router.delete("/entries/{eid}")
async def del_pers(eid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_entry(eid, u["id"], db)

@router.get("/accounts")
async def get_accounts(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalAccountModel, u["id"], db)
@router.post("/accounts")
async def create_account(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalAccountModel, _ACCOUNT_COLUMNS, "pacc", d, u["id"], db)
@router.delete("/accounts/{aid}")
async def del_account(aid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_owned(PersonalAccountModel, aid, u["id"], db)

@router.get("/budgets")
async def get_budgets(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalBudgetModel, u["id"], db)
@router.post("/budgets")
async def create_budget(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalBudgetModel, _BUDGET_COLUMNS, "pbud", d, u["id"], db, defaults={"spent_amount": 0.0})
@router.delete("/budgets/{bid}")
async def del_budget(bid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_owned(PersonalBudgetModel, bid, u["id"], db)

@router.get("/goals")
async def get_goals(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalGoalModel, u["id"], db)
@router.post("/goals")
async def create_goal(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalGoalModel, _GOAL_COLUMNS, "pgoal", d, u["id"], db, defaults={"current_amount": 0.0})
@router.post("/goals/{gid}/contribute")
async def contribute_goal(gid:str,d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    g = await db.get(PersonalGoalModel, gid)
    if not g or g.owner_id != u["id"]: raise HTTPException(404)
    g.current_amount = round((g.current_amount or 0) + d.get("amount", 0), 2)
    await db.commit()
    await db.refresh(g)
    return model_to_dict(g)
@router.delete("/goals/{gid}")
async def del_goal(gid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_owned(PersonalGoalModel, gid, u["id"], db)

@router.get("/debts")
async def get_debts(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalDebtModel, u["id"], db)
@router.post("/debts")
async def create_debt(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalDebtModel, _DEBT_COLUMNS, "pdebt", d, u["id"], db, defaults={"installments_paid": 0})
@router.delete("/debts/{did}")
async def del_debt(did:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_owned(PersonalDebtModel, did, u["id"], db)

@router.get("/subscriptions")
async def get_subs(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalSubscriptionModel, u["id"], db)
@router.post("/subscriptions")
async def create_sub(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalSubscriptionModel, _SUBSCRIPTION_COLUMNS, "psub", d, u["id"], db, defaults={"is_active": True})
@router.delete("/subscriptions/{sid}")
async def del_sub(sid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_owned(PersonalSubscriptionModel, sid, u["id"], db)

@router.get("/splits")
async def get_splits(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _list_owned(PersonalSplitModel, u["id"], db)
@router.post("/splits")
async def create_split(d:dict,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _create_owned(PersonalSplitModel, _SPLIT_COLUMNS, "psplit", d, u["id"], db)
@router.delete("/splits/{spid}")
async def del_split(spid:str,u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _delete_owned(PersonalSplitModel, spid, u["id"], db)

_MONTHS_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


async def _net_worth_series(owner_id: str, entries: list[dict], db: AsyncSession, months: int = 6) -> list[dict]:
    """Net worth today = account balances (cards are negative) - remaining debt.
    Each earlier month-end is rebuilt by undoing the entries recorded after it."""
    accounts = await _list_owned(PersonalAccountModel, owner_id, db)
    debts = await _list_owned(PersonalDebtModel, owner_id, db)
    current = sum(a.get("balance") or 0 for a in accounts) - sum(d.get("remaining_amount") or 0 for d in debts)

    def signed(e: dict) -> float:
        return (e.get("amount") or 0) * (1 if e.get("type") == "RECEITA" else -1)

    today = date.today()
    series = []
    for back in range(months - 1, -1, -1):
        y, m = today.year, today.month - back
        while m <= 0:
            m += 12
            y -= 1
        next_month = date(y + (m == 12), m % 12 + 1, 1).isoformat()
        after = sum(signed(e) for e in entries if (e.get("date") or "") >= next_month)
        series.append({"month": _MONTHS_PT[m - 1], "value": round(current - after, 2)})
    return series


@router.get("/analytics")
async def get_analytics(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonalEntryModel).where(PersonalEntryModel.owner_id == u["id"]))
    entries = models_to_dicts(result.scalars().all())
    total_by_cat: dict = {}
    for e in entries:
        if e["type"] == "DESPESA":
            total_by_cat[e["category"]] = total_by_cat.get(e["category"], 0) + e["amount"]
    net_worth_series = await _net_worth_series(u["id"], entries, db)
    return {"spend_by_category": [{"category": k, "total": round(v, 2)} for k, v in total_by_cat.items()], "net_worth_series": net_worth_series}

SYSTEM_PERSONAL = (
    "Você é o CFO Pessoal do TechConnect, consultor de finanças pessoais. Responda em português do Brasil, "
    "com valores em reais (R$), usando somente os dados fornecidos em JSON. Nunca invente números."
)


@router.post("/ai/insights")
async def personal_ai_insights(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), llm: Llm | None = Depends(get_llm)):
    snapshot = await personal_snapshot(db, u["id"])
    prompt = (
        f"Dados financeiros da pessoa:\n{json.dumps(snapshot, ensure_ascii=False)}\n\n"
        'Devolva JSON {"insights": [{"type": "ALERT" | "OPPORTUNITY" | "CUT", "message": "...", "impact_value": número em reais}]} '
        "com 3 a 5 itens concretos e acionáveis."
    )
    reply, reason = await ai_service.ask(db, u, llm, SYSTEM_PERSONAL, prompt, as_json=True)
    insights, source = None, "regra"
    if reply:
        try:
            data = parse_json(reply)
            insights = [
                {"type": i["type"], "message": str(i["message"])[:500], "impact_value": round(float(i.get("impact_value") or 0), 2)}
                for i in data.get("insights", []) if i.get("type") in ("ALERT", "OPPORTUNITY", "CUT") and i.get("message")
            ][:6] or None
            source = "ia" if insights else "regra"
        except (LlmUnavailable, AttributeError, TypeError, ValueError):
            insights = None
    if insights is None:
        insights = rules.personal_insights(snapshot)
    await db.commit()
    return {"insights": insights, "source": source}
