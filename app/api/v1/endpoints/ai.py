# NOTA: Rotas /ai: CFO Virtual (chat e histórico), conciliação por IA e gerador de orçamento.
#       Usa o Gemini sobre os dados reais da empresa; sem Gemini, responde por regras (app/integrations/ai).

"""CFO Virtual (business AI). Answers come from Gemini over the company's real snapshot, or from
rules over the same snapshot when the model is unavailable or the plan's quota is spent (IA-1)."""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.models import AiMessageModel, BankTransactionModel, CategoryModel, FinancialEntryModel
from app.db.session import get_db
from app.db.utils import models_to_dicts
from app.integrations.ai import rules
from app.integrations.ai import service as ai_service
from app.integrations.ai.context import business_snapshot
from app.integrations.ai.llm import Llm, LlmUnavailable, get_llm, parse_json

router = APIRouter()

SYSTEM_CFO = (
    "Você é o CFO Virtual do TechConnect, consultor financeiro de pequenas e médias empresas brasileiras. "
    "Responda em português do Brasil, de forma objetiva e prática, com valores em reais (R$). "
    "Use somente os dados da empresa fornecidos em JSON; se faltar informação, diga o que falta em vez de supor. "
    "Nunca invente números."
)


def _dumps(data) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


# ---------- chat ----------

class ChatReq(BaseModel):
    message: str


@router.post("/chat")
async def ai_chat(b: ChatReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), llm: Llm | None = Depends(get_llm)):
    message = b.message.strip()[:2000]
    if not message:
        raise HTTPException(400, "Escreva uma pergunta")
    snapshot = await business_snapshot(db, u["company_id"])
    recent = (await db.execute(
        select(AiMessageModel).where(AiMessageModel.user_id == u["id"]).order_by(AiMessageModel.created_at.desc()).limit(10)
    )).scalars().all()
    conversation = "\n".join(f"{'Usuário' if m.role == 'user' else 'CFO'}: {m.content}" for m in reversed(recent))
    prompt = f"Dados da empresa:\n{_dumps(snapshot)}\n\nConversa recente:\n{conversation or '(início)'}\n\nPergunta atual: {message}"

    reply, reason = await ai_service.ask(db, u, llm, SYSTEM_CFO, prompt)
    if reply:
        text, source, model = reply.text, "ia", reply.model
    else:
        note = ai_service.FALLBACK_NOTE[reason]
        text = (note + "\n\n" if note else "") + rules.business_chat(snapshot, message)
        source, model = "regra", None

    now = datetime.utcnow()
    for role, content, created in (("user", message, now.isoformat()), ("assistant", text, now.replace(microsecond=min(now.microsecond + 1, 999999)).isoformat())):
        db.add(AiMessageModel(id=f"aim-{uuid.uuid4().hex}", company_id=u["company_id"], user_id=u["id"], role=role,
                              content=content, source=source if role == "assistant" else None, model=model, created_at=created))
    await db.commit()
    return {"response": text, "source": source, "model": model or "regras"}


@router.get("/history")
async def ai_hist(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(AiMessageModel).where(AiMessageModel.user_id == u["id"]).order_by(AiMessageModel.created_at.desc()).limit(100)
    )).scalars().all()
    items = models_to_dicts(list(reversed(rows)))
    return {"items": items, "total": len(items)}


# ---------- CFO insights ----------

_INSIGHT_TYPES, _LEVELS_IMPACT, _LEVELS_URGENCY = {"OPORTUNIDADE", "ALERTA"}, {"Alto", "Medio", "Baixo"}, {"Alta", "Media", "Baixa"}


def _valid_insights(data) -> list[dict]:
    items = data.get("insights") if isinstance(data, dict) else None
    out = []
    for it in items or []:
        if isinstance(it, dict) and it.get("type") in _INSIGHT_TYPES and it.get("title") and it.get("description"):
            out.append({
                "type": it["type"], "title": str(it["title"])[:120], "description": str(it["description"])[:600],
                "impact": it.get("impact") if it.get("impact") in _LEVELS_IMPACT else "Medio",
                "urgency": it.get("urgency") if it.get("urgency") in _LEVELS_URGENCY else "Media",
            })
    if not out:
        raise LlmUnavailable("insights inválidos")
    return out[:6]


@router.post("/consultant/cfo")
async def ai_cfo(u=Depends(get_current_user), db: AsyncSession = Depends(get_db), llm: Llm | None = Depends(get_llm)):
    snapshot = await business_snapshot(db, u["company_id"])
    prompt = (
        f"Dados da empresa:\n{_dumps(snapshot)}\n\n"
        'Analise e devolva JSON no formato {"insights": [{"type": "OPORTUNIDADE" ou "ALERTA", "title": "...", '
        '"description": "...", "impact": "Alto"|"Medio"|"Baixo", "urgency": "Alta"|"Media"|"Baixa"}]} '
        "com 3 a 5 itens concretos, citando valores dos dados."
    )
    reply, reason = await ai_service.ask(db, u, llm, SYSTEM_CFO, prompt, as_json=True)
    insights, source = None, "regra"
    if reply:
        try:
            insights, source = _valid_insights(parse_json(reply)), "ia"
        except LlmUnavailable:
            reason = "erro"
    if insights is None:
        insights = rules.business_insights(snapshot)
    await db.commit()
    return {"insights": insights, "source": source, "note": ai_service.FALLBACK_NOTE.get(reason or "", "") if source == "regra" else ""}


# ---------- category suggestions for bank transactions ----------

class ConciliationReq(BaseModel):
    limit: int = 30


@router.post("/consultant/conciliation")
async def ai_conc(b: ConciliationReq | None = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), llm: Llm | None = Depends(get_llm)):
    """Suggests categories for the company's unreconciled, uncategorized bank transactions."""
    limit = max(1, min((b or ConciliationReq()).limit, 50))
    txs = (await db.execute(
        select(BankTransactionModel).where(
            BankTransactionModel.company_id == u["company_id"], BankTransactionModel.owner_id.is_(None),
            BankTransactionModel.status == "NOVA", BankTransactionModel.category.is_(None),
        ).order_by(BankTransactionModel.date.desc()).limit(limit)
    )).scalars().all()
    if not txs:
        return {"results": [], "source": "regra"}
    used = (await db.execute(select(FinancialEntryModel.category).where(FinancialEntryModel.company_id == u["company_id"]).distinct())).scalars().all()
    registered = (await db.execute(select(CategoryModel.name).where(CategoryModel.company_id == u["company_id"]))).scalars().all()
    known = sorted({c for c in [*used, *registered] if c})

    suggestions: dict[str, tuple[str, float]] = {}
    source = "regra"
    prompt = (
        f"Categorias já usadas pela empresa: {_dumps(known)}\n"
        f"Movimentações: {_dumps([{'id': t.id, 'descricao': t.description, 'valor': t.amount} for t in txs])}\n\n"
        'Devolva JSON {"sugestoes": [{"id": "...", "categoria": "...", "confianca": 0.0 a 1.0}]}. '
        "Prefira as categorias já usadas; crie uma nova curta só se nenhuma servir."
    )
    reply, _ = await ai_service.ask(db, u, llm, SYSTEM_CFO, prompt, as_json=True)
    if reply:
        try:
            for s in parse_json(reply).get("sugestoes", []):
                if s.get("id") and s.get("categoria"):
                    suggestions[s["id"]] = (str(s["categoria"])[:100], float(s.get("confianca") or 0.7))
            source = "ia"
        except (LlmUnavailable, AttributeError, TypeError, ValueError):
            suggestions = {}
    results = []
    for t in txs:
        category, confidence = suggestions.get(t.id) or rules.suggest_category(t.description or "", known)
        results.append({"id": t.id, "description": t.description, "amount": t.amount, "date": t.date,
                        "suggested_category": category, "confidence": round(confidence, 2), "status": "SUGERIDO" if category else "SEM_SUGESTAO"})
    await db.commit()
    return {"results": results, "source": source}


# ---------- proposal generator ----------

class ProposalReq(BaseModel):
    briefing: str
    markup: float = 40.0


@router.post("/consultant/proposal")
async def ai_prop(b: ProposalReq, u=Depends(get_current_user), db: AsyncSession = Depends(get_db), llm: Llm | None = Depends(get_llm)):
    briefing = b.briefing.strip()[:4000]
    if not briefing:
        raise HTTPException(400, "Descreva o projeto no briefing")
    if not 0 <= b.markup <= 500:
        raise HTTPException(400, "Markup deve estar entre 0% e 500%")
    team = (await business_snapshot(db, u["company_id"]))["equipe"]
    hourly = team["custo_hora_medio"]
    if not hourly:
        raise HTTPException(400, "Cadastre colaboradores com salário para calcular o custo-hora da equipe")
    prompt = (
        f"Briefing do projeto: {briefing}\nA equipe tem {team['colaboradores_ativos']} pessoa(s).\n\n"
        'Estime o esforço e devolva JSON {"etapas": [{"nome": "...", "horas": número}], "premissas": ["..."]}. '
        "Seja realista para uma PME brasileira; não inclua valores em dinheiro."
    )
    reply, reason = await ai_service.ask(db, u, llm, SYSTEM_CFO, prompt, as_json=True)
    await db.commit()
    if not reply:
        raise HTTPException(503, "A estimativa de horas depende da IA, que está indisponível agora" if reason != "cota"
                            else "Limite mensal de perguntas à IA do seu plano atingido")
    try:
        data = parse_json(reply)
        steps = [{"nome": str(s["nome"])[:80], "horas": round(float(s["horas"]), 1)} for s in data.get("etapas", []) if float(s.get("horas", 0)) > 0]
    except (LlmUnavailable, KeyError, TypeError, ValueError, AttributeError):
        steps = []
    if not steps:
        raise HTTPException(503, "A IA não devolveu uma estimativa utilizável; tente detalhar o briefing")
    hours = round(sum(s["horas"] for s in steps), 1)
    cost = round(hours * hourly, 2)
    price = round(cost * (1 + b.markup / 100), 2)
    return {
        "estimated_hours": hours, "hourly_cost": hourly, "estimated_internal_cost": cost, "suggested_price": price,
        "margin_percentage": round((price - cost) / price * 100, 1) if price else 0.0,
        "breakdown": steps, "assumptions": [str(a)[:200] for a in (data.get("premissas") or [])][:6], "source": "ia",
    }
