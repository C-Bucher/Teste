"""Bank accounts, statement import, aggregator connections and reconciliation (BANK-1).

`scope=empresa` works on the company's books (plan Empresarial/Completo + module financeiro);
`scope=pessoal` works on the signed-in person's Hub Pessoal (plan Pessoal/Completo).
"""

import os
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit
from app.core.notify import notify_company
from app.core.permissions import get_allowed_modules
from app.core.plans import bank_connections_used, current_plan
from app.core.security import get_current_user
from app.db.models import BankAccountModel, BankTransactionModel, CategorizationRuleModel, FinancialEntryModel
from app.db.session import get_db
from app.db.utils import model_to_dict, models_to_dicts
from app.integrations.bank import service
from app.integrations.ai.service import usage as ai_usage
from app.integrations.bank.providers import BankProvider, ProviderError, get_bank_provider
from app.integrations.bank.statement import StatementError, parse_statement

router = APIRouter()

MAX_STATEMENT_BYTES = 5 * 1024 * 1024
SCOPES = ("empresa", "pessoal")


async def _owner_for(scope: str, u: dict, db: AsyncSession) -> dict:
    """Checks the user may work in this scope and returns the ownership columns for it."""
    if scope == "empresa":
        if u.get("plan_scope") not in ("empresarial", "completo"):
            raise HTTPException(403, "Seu plano não inclui o Hub Empresarial")
        if "financeiro" not in await get_allowed_modules(u, db):
            raise HTTPException(403, "Seu cargo não tem acesso ao módulo financeiro")
        return {"company_id": u["company_id"], "owner_id": None}
    if scope == "pessoal":
        if u.get("plan_scope") not in ("pessoal", "completo"):
            raise HTTPException(403, "Seu plano não inclui o Hub Pessoal")
        return {"company_id": None, "owner_id": u["id"]}
    raise HTTPException(400, "Escopo inválido. Use empresa ou pessoal")


def _scope_of(obj, u: dict) -> str | None:
    if obj.owner_id and obj.owner_id == u["id"]:
        return "pessoal"
    if obj.owner_id is None and obj.company_id and obj.company_id == u["company_id"]:
        return "empresa"
    return None


async def _load(db: AsyncSession, model, oid: str, u: dict):
    """Loads a bank row the user owns (404 otherwise) and enforces the permissions of its scope."""
    obj = await db.get(model, oid)
    scope = _scope_of(obj, u) if obj else None
    if not scope:
        raise HTTPException(404, "Não encontrado")
    await _owner_for(scope, u, db)
    return obj


def _where(model, owner: dict):
    return (model.company_id == owner["company_id"]) if owner["company_id"] else (model.owner_id == owner["owner_id"])


# ---------- accounts ----------

@router.get("/accounts")
async def list_accounts(scope: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    owner = await _owner_for(scope, u, db)
    rows = (await db.execute(select(BankAccountModel).where(_where(BankAccountModel, owner)).order_by(BankAccountModel.created_at))).scalars().all()
    return models_to_dicts(rows)


@router.delete("/accounts/{aid}")
async def delete_account(aid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    account = await _load(db, BankAccountModel, aid, u)
    await db.execute(delete(BankTransactionModel).where(BankTransactionModel.bank_account_id == aid))
    await db.delete(account)
    audit.record_by(db, u, "CONTA_BANCARIA_REMOVIDA", entity="bank_account", entity_id=aid, details={"nome": account.name})
    await db.commit()
    return {"success": True}


async def _new_account(db: AsyncSession, owner: dict, scope: str, name: str, **extra) -> BankAccountModel:
    account = BankAccountModel(id=f"bac-{uuid.uuid4().hex[:12]}", scope=scope, name=name[:255], **owner, **extra)
    db.add(account)
    await db.flush()
    return account


# ---------- statement import ----------

@router.post("/import")
async def import_statement(
    scope: str = Form(...),
    file: UploadFile = File(...),
    account_id: str | None = Form(None),
    account_name: str | None = Form(None),
    u=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner = await _owner_for(scope, u, db)
    content = await file.read(MAX_STATEMENT_BYTES + 1)
    if len(content) > MAX_STATEMENT_BYTES:
        raise HTTPException(413, "Extrato maior que 5 MB")
    try:
        statement = parse_statement(content, os.path.basename(file.filename or "extrato"))
    except StatementError as e:
        raise HTTPException(400, str(e))

    if account_id:
        account = await _load(db, BankAccountModel, account_id, u)
        if account.scope != scope:
            raise HTTPException(400, "A conta pertence a outro escopo")
    else:
        # OFX carries bank + account number: re-importing the same account must not create a twin.
        identity = f"{statement.bank_id or ''}:{statement.account_id}" if statement.account_id else None
        account = (await db.execute(select(BankAccountModel).where(
            _where(BankAccountModel, owner), BankAccountModel.source == "arquivo", BankAccountModel.provider_account_id == identity,
        ))).scalars().first() if identity else None
        if account is None:
            default_name = f"Conta {statement.account_id}" if statement.account_id else "Conta importada"
            account = await _new_account(db, owner, scope, account_name or default_name,
                                         bank_name=f"Banco {statement.bank_id}" if statement.bank_id else None,
                                         source="arquivo", provider_account_id=identity)

    result = await service.ingest(db, account, statement.transactions, u)
    account.last_sync_at = datetime.utcnow().isoformat()
    audit.record_by(db, u, "EXTRATO_IMPORTADO", entity="bank_account", entity_id=account.id,
                    details={"arquivo": file.filename, **result})
    if scope == "empresa" and result["imported"]:
        pending = result["imported"] - result["reconciled"]
        await notify_company(db, u["company_id"], "Extrato importado",
                             f"{account.name}: {result['imported']} movimentação(ões) nova(s), {result['reconciled']} conciliada(s) "
                             f"automaticamente e {pending} aguardando você em Bancos.")
    await db.commit()
    await db.refresh(account)
    return {"account": model_to_dict(account), **result}


# ---------- transactions ----------

@router.get("/transactions")
async def list_transactions(scope: str, status: str | None = None, account_id: str | None = None,
                            u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    owner = await _owner_for(scope, u, db)
    q = select(BankTransactionModel).where(_where(BankTransactionModel, owner))
    if status:
        q = q.where(BankTransactionModel.status == status)
    if account_id:
        q = q.where(BankTransactionModel.bank_account_id == account_id)
    rows = (await db.execute(q.order_by(BankTransactionModel.date.desc(), BankTransactionModel.created_at.desc()).limit(1000))).scalars().all()
    return models_to_dicts(rows)


async def _load_new_business_tx(db: AsyncSession, tid: str, u: dict) -> BankTransactionModel:
    tx = await _load(db, BankTransactionModel, tid, u)
    if tx.company_id is None:
        raise HTTPException(400, "Transações pessoais já entram como lançamentos no Hub Pessoal")
    if tx.status != "NOVA":
        raise HTTPException(400, "Esta transação já foi tratada")
    return tx


class CreateEntryReq(BaseModel):
    category: str | None = None
    description: str | None = None


@router.post("/transactions/{tid}/create-entry")
async def create_entry_from_tx(tid: str, b: CreateEntryReq | None = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tx = await _load_new_business_tx(db, tid, u)
    b = b or CreateEntryReq()
    entry = FinancialEntryModel(
        id=f"fin-{uuid.uuid4().hex[:10]}", company_id=tx.company_id,
        type="RECEITA" if tx.amount > 0 else "DESPESA", amount=abs(tx.amount),
        description=b.description or tx.description, category=b.category or tx.category,
        due_date=tx.date, payment_date=tx.date, status="PAGO",
    )
    db.add(entry)
    tx.status, tx.entry_id = "LANCADA", entry.id
    if b.category:
        tx.category = b.category
    audit.record_by(db, u, "LANCAMENTO_CRIADO", entity="financial_entry", entity_id=entry.id,
                    details={"origem": "extrato", "transacao": tx.id, "valor": entry.amount})
    await db.commit()
    return {**model_to_dict(tx)}


class MatchReq(BaseModel):
    entry_id: str


@router.post("/transactions/{tid}/match")
async def match_tx(tid: str, b: MatchReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tx = await _load_new_business_tx(db, tid, u)
    entry = await db.get(FinancialEntryModel, b.entry_id)
    if not entry or entry.company_id != tx.company_id:
        raise HTTPException(404, "Lançamento não encontrado")
    if entry.status != "PENDENTE":
        raise HTTPException(400, "O lançamento já está pago")
    if not service.amounts_match(tx.amount, entry):
        raise HTTPException(400, "Tipo ou valor do lançamento não confere com a transação")
    service.mark_paid(db, entry, tx, u, automatic=False)
    await db.commit()
    return model_to_dict(tx)


class CategoryReq(BaseModel):
    category: str
    create_rule: bool = False


@router.post("/transactions/{tid}/category")
async def set_tx_category(tid: str, b: CategoryReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Applies a category (e.g. one suggested by the AI); optionally remembers it as a rule."""
    tx = await _load(db, BankTransactionModel, tid, u)
    category = b.category.strip()[:100]
    if not category:
        raise HTTPException(400, "Informe a categoria")
    tx.category = category
    if b.create_rule and tx.description:
        owner = {"company_id": tx.company_id, "owner_id": None} if tx.owner_id is None else {"company_id": None, "owner_id": tx.owner_id}
        pattern = tx.description.strip()[:100].lower()
        db.add(CategorizationRuleModel(id=f"rule-{uuid.uuid4().hex[:10]}", pattern=pattern, category=category, **owner))
    await db.commit()
    return model_to_dict(tx)


@router.post("/transactions/{tid}/ignore")
async def ignore_tx(tid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tx = await _load(db, BankTransactionModel, tid, u)
    if tx.status != "NOVA":
        raise HTTPException(400, "Esta transação já foi tratada")
    tx.status = "IGNORADA"
    await db.commit()
    return model_to_dict(tx)


# ---------- categorization rules ----------

class RuleReq(BaseModel):
    scope: str
    pattern: str
    category: str


@router.get("/rules")
async def list_rules(scope: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    owner = await _owner_for(scope, u, db)
    return models_to_dicts((await db.execute(select(CategorizationRuleModel).where(_where(CategorizationRuleModel, owner)))).scalars().all())


@router.post("/rules")
async def create_rule(b: RuleReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    owner = await _owner_for(b.scope, u, db)
    if not b.pattern.strip() or not b.category.strip():
        raise HTTPException(400, "Informe o texto e a categoria")
    rule = CategorizationRuleModel(id=f"rule-{uuid.uuid4().hex[:10]}", pattern=b.pattern.strip()[:100], category=b.category.strip()[:100], **owner)
    db.add(rule)
    await db.commit()
    return model_to_dict(rule)


@router.delete("/rules/{rid}")
async def delete_rule(rid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rule = await _load(db, CategorizationRuleModel, rid, u)
    await db.delete(rule)
    await db.commit()
    return {"success": True}


# ---------- aggregator (Open Finance) ----------

def _require_provider(provider: BankProvider | None) -> BankProvider:
    if provider is None:
        raise HTTPException(503, "Conexão automática com bancos ainda não está disponível. Use a importação de extrato (OFX/CSV)")
    return provider


async def _check_connection_limit(db: AsyncSession, u: dict, adding: int) -> None:
    plan = await current_plan(db, u)
    limit = plan["limits"].get("bank_connections", 0)
    used = await bank_connections_used(db, u)
    if used + adding > limit:
        raise HTTPException(402, f"Seu plano {plan['name']} permite {limit} conta(s) conectada(s) e você já usa {used}. Faça upgrade para conectar mais")


class ScopeReq(BaseModel):
    scope: str


@router.post("/connect-token")
async def connect_token(b: ScopeReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db),
                        provider: BankProvider | None = Depends(get_bank_provider)):
    await _owner_for(b.scope, u, db)
    provider = _require_provider(provider)
    await _check_connection_limit(db, u, adding=1)
    try:
        token = await provider.create_connect_token(u["id"])
    except ProviderError as e:
        raise HTTPException(502, str(e))
    return {"connect_token": token, "provider": provider.name}


class ConnectionReq(BaseModel):
    scope: str
    item_id: str


@router.post("/connections")
async def register_connection(b: ConnectionReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db),
                              provider: BankProvider | None = Depends(get_bank_provider)):
    """Called after the person authorizes the bank in the aggregator widget."""
    owner = await _owner_for(b.scope, u, db)
    provider = _require_provider(provider)
    try:
        remote = await provider.list_accounts(b.item_id)
    except ProviderError as e:
        raise HTTPException(502, str(e))
    known = set((await db.execute(
        select(BankAccountModel.provider_account_id).where(_where(BankAccountModel, owner), BankAccountModel.source == "agregador")
    )).scalars().all())
    fresh = [a for a in remote if a.id not in known]
    await _check_connection_limit(db, u, adding=len(fresh))
    created = []
    for a in fresh:
        created.append(await _new_account(db, owner, b.scope, a.name, bank_name=a.bank_name, source="agregador",
                                          provider=provider.name, provider_item_id=b.item_id, provider_account_id=a.id))
    audit.record_by(db, u, "BANCO_CONECTADO", entity="bank_connection", entity_id=b.item_id, details={"contas": len(created)})
    await db.commit()
    return models_to_dicts(created)


@router.post("/accounts/{aid}/sync")
async def sync_account(aid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db),
                       provider: BankProvider | None = Depends(get_bank_provider)):
    account = await _load(db, BankAccountModel, aid, u)
    if account.source != "agregador":
        raise HTTPException(400, "Esta conta é alimentada por importação de extrato")
    provider = _require_provider(provider)
    # Overlap a few days so late-posted transactions are not missed; duplicates are skipped anyway.
    since = (date.fromisoformat(account.last_sync_at[:10]) - timedelta(days=3)) if account.last_sync_at else date.today() - timedelta(days=90)
    try:
        parsed = await provider.list_transactions(account.provider_account_id, since)
    except ProviderError as e:
        account.status = "ERRO"
        await db.commit()
        raise HTTPException(502, str(e))
    result = await service.ingest(db, account, parsed, u)
    account.last_sync_at = datetime.utcnow().isoformat()
    account.status = "ATIVA"
    await db.commit()
    return result


@router.get("/usage")
async def usage(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    plan = await current_plan(db, u)
    ai = await ai_usage(db, u)
    await db.commit()
    return {
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "bank_connections": {"used": await bank_connections_used(db, u), "limit": plan["limits"].get("bank_connections", 0)},
        "ai_queries": ai,
    }
