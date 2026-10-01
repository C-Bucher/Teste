"""One gate for model calls: availability, plan quota (LIM-1) and usage counting."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import current_plan
from app.db.models import AiUsageModel
from app.integrations.ai.llm import Llm, LlmReply, LlmUnavailable


async def _usage_row(db: AsyncSession, company_id: str) -> AiUsageModel:
    period = date.today().strftime("%Y-%m")
    row = (await db.execute(select(AiUsageModel).where(AiUsageModel.company_id == company_id, AiUsageModel.period == period))).scalar_one_or_none()
    if row is None:
        row = AiUsageModel(id=f"aiu-{uuid.uuid4().hex[:12]}", company_id=company_id, period=period, count=0)
        db.add(row)
        await db.flush()
    return row


async def usage(db: AsyncSession, u: dict) -> dict:
    plan = await current_plan(db, u)
    row = await _usage_row(db, u["company_id"])
    return {"used": row.count, "limit": plan["limits"].get("ai_queries", 0)}


async def ask(db: AsyncSession, u: dict, llm: Llm | None, system: str, prompt: str, *, as_json: bool = False) -> tuple[LlmReply | None, str | None]:
    """Returns (reply, None) or (None, reason) with reason in sem_ia | cota | erro. Caller commits."""
    if llm is None:
        return None, "sem_ia"
    plan = await current_plan(db, u)
    limit = plan["limits"].get("ai_queries", 0)
    row = await _usage_row(db, u["company_id"])
    if limit != -1 and row.count >= limit:
        return None, "cota"
    try:
        reply = await llm.generate(system, prompt, as_json=as_json)
    except LlmUnavailable:
        return None, "erro"
    row.count += 1
    return reply, None


FALLBACK_NOTE = {
    "sem_ia": "",
    "cota": "Limite mensal de perguntas à IA do seu plano atingido; resposta calculada pelas regras do sistema.",
    "erro": "A IA não respondeu agora; resposta calculada pelas regras do sistema.",
}
