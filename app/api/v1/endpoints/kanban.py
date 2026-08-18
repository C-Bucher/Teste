from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
import time
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import (
    ClientModel,
    ProjectModel,
    KanbanColumnModel,
    KanbanCardModel,
    CardCommentModel,
    EmployeeModel,
)
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_CLIENT_COLUMNS = {c.name for c in ClientModel.__table__.columns}
_PROJECT_COLUMNS = {c.name for c in ProjectModel.__table__.columns}
_COLUMN_COLUMNS = {c.name for c in KanbanColumnModel.__table__.columns}
_CARD_COLUMNS = {c.name for c in KanbanCardModel.__table__.columns}

# ACTIVE_TIMERS is transient "timer running right now" state, not durable
# data. It intentionally lives as a plain in-memory dict in this module —
# losing it on a backend restart is expected and accepted.
# card_id -> {started_at, employee_id, timer_id}
ACTIVE_TIMERS: dict = {}


@router.get("/templates")
async def get_kanban_templates(u=Depends(get_current_user)):
    return []


@router.get("/clients")
async def get_clis(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClientModel))
    return models_to_dicts(result.scalars().all())


@router.post("/clients")
async def create_cli(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cli_dict = {"id": f"cli-{uuid.uuid4().hex[:6]}", **d}
    model_kwargs = {k: v for k, v in cli_dict.items() if k in _CLIENT_COLUMNS}
    cli = ClientModel(**model_kwargs)
    db.add(cli)
    await db.commit()
    await db.refresh(cli)
    return model_to_dict(cli)


@router.put("/clients/{cid}")
async def upd_cli(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cli = await db.get(ClientModel, cid)
    if not cli:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _CLIENT_COLUMNS:
            setattr(cli, k, v)
    await db.commit()
    await db.refresh(cli)
    return model_to_dict(cli)


@router.get("/projects")
async def get_projs(client_id: Optional[str] = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(ProjectModel)
    if client_id:
        q = q.where(ProjectModel.client_id == client_id)
    result = await db.execute(q)
    return models_to_dicts(result.scalars().all())


@router.post("/projects")
async def create_proj(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    proj_dict = {"id": f"proj-{uuid.uuid4().hex[:6]}", "status": "PLANEJAMENTO", **d}
    model_kwargs = {k: v for k, v in proj_dict.items() if k in _PROJECT_COLUMNS}
    proj = ProjectModel(**model_kwargs)
    db.add(proj)
    await db.flush()

    default_columns = [
        {"id": f"col-{uuid.uuid4().hex[:4]}", "name": "Backlog", "order": 1},
        {"id": f"col-{uuid.uuid4().hex[:4]}", "name": "Em Andamento", "order": 2},
        {"id": f"col-{uuid.uuid4().hex[:4]}", "name": "Concluido", "order": 3},
    ]
    for col in default_columns:
        db.add(KanbanColumnModel(id=col["id"], project_id=proj.id, name=col["name"], order=col["order"]))

    await db.commit()
    await db.refresh(proj)
    return model_to_dict(proj)


@router.get("/projects/{pid}/board")
async def get_board(pid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    proj = await db.get(ProjectModel, pid)
    cli = await db.get(ClientModel, proj.client_id) if proj and proj.client_id else None

    columns_result = await db.execute(
        select(KanbanColumnModel).where(KanbanColumnModel.project_id == pid).order_by(KanbanColumnModel.order)
    )
    columns = columns_result.scalars().all()

    columns_out = []
    for col in columns:
        cards_result = await db.execute(select(KanbanCardModel).where(KanbanCardModel.column_id == col.id))
        cards = cards_result.scalars().all()

        cards_out = []
        for card in cards:
            comments_result = await db.execute(
                select(CardCommentModel).where(CardCommentModel.card_id == card.id).order_by(CardCommentModel.created_at)
            )
            card_dict = model_to_dict(card)
            card_dict["comments"] = models_to_dicts(comments_result.scalars().all())
            cards_out.append(card_dict)

        col_dict = model_to_dict(col)
        col_dict["cards"] = cards_out
        columns_out.append(col_dict)

    return {
        "project": model_to_dict(proj) if proj else None,
        "client": model_to_dict(cli) if cli else None,
        "columns": columns_out,
    }


@router.post("/projects/{pid}/columns")
async def add_col(pid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    count_result = await db.execute(select(KanbanColumnModel).where(KanbanColumnModel.project_id == pid))
    existing_count = len(count_result.scalars().all())

    col_dict = {"id": f"col-{uuid.uuid4().hex[:6]}", "project_id": pid, "order": existing_count + 1, **d}
    model_kwargs = {k: v for k, v in col_dict.items() if k in _COLUMN_COLUMNS}
    col = KanbanColumnModel(**model_kwargs)
    db.add(col)
    await db.commit()
    await db.refresh(col)

    result = model_to_dict(col)
    result["cards"] = []
    return result


@router.post("/cards")
async def create_card(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    col_id = d.get("column_id")
    col = await db.get(KanbanColumnModel, col_id) if col_id else None
    if not col:
        raise HTTPException(404, "Coluna nao encontrada")

    card_dict = {
        "id": f"card-{uuid.uuid4().hex[:6]}",
        "cost_per_task": 0,
        "total_time_seconds": 0,
        "status": "ABERTO",
        **d,
    }
    model_kwargs = {k: v for k, v in card_dict.items() if k in _CARD_COLUMNS}
    card = KanbanCardModel(**model_kwargs)
    db.add(card)
    await db.commit()
    await db.refresh(card)

    result = model_to_dict(card)
    result["comments"] = []
    return result


@router.post("/cards/{cid}/move")
async def move_card(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await db.get(KanbanCardModel, cid)
    if not card:
        raise HTTPException(404)

    new_col = d.get("column_id")
    if new_col:
        col = await db.get(KanbanColumnModel, new_col)
        if not col:
            raise HTTPException(404, "Coluna de destino nao encontrada")
        card.column_id = new_col
        await db.commit()

    return {"id": cid, "column_id": new_col, "moved": True}


@router.put("/cards/{cid}")
async def upd_card(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await db.get(KanbanCardModel, cid)
    if not card:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _CARD_COLUMNS:
            setattr(card, k, v)
    await db.commit()
    await db.refresh(card)
    return model_to_dict(card)


@router.delete("/cards/{cid}")
async def del_card(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await db.get(KanbanCardModel, cid)
    if card:
        comments_result = await db.execute(select(CardCommentModel).where(CardCommentModel.card_id == cid))
        for comment in comments_result.scalars().all():
            await db.delete(comment)
        await db.delete(card)
        await db.commit()
    return {"success": True}


@router.post("/cards/{cid}/time/start")
async def start_timer(cid: str, u=Depends(get_current_user)):
    ACTIVE_TIMERS[cid] = {"started_at": time.time(), "employee_id": u["id"], "timer_id": f"tmr-{uuid.uuid4().hex[:8]}"}
    return {"card_id": cid, "started_at": datetime.now().isoformat()}


@router.post("/cards/{cid}/time/stop")
async def stop_timer(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = ACTIVE_TIMERS.pop(cid, None)
    elapsed = int(time.time() - t["started_at"]) if t else 3600

    card = await db.get(KanbanCardModel, cid)
    if card:
        card.total_time_seconds = (card.total_time_seconds or 0) + elapsed
        emp = None
        if card.assignee_id:
            emp = await db.get(EmployeeModel, card.assignee_id)
        rate = emp.hourly_rate if emp and emp.hourly_rate else 85
        card.cost_per_task = round(card.total_time_seconds / 3600 * rate, 2)
        await db.commit()

    return {"card_id": cid, "total_time_seconds": elapsed, "cost_per_task": round(elapsed / 3600 * 85, 2)}


@router.post("/cards/{cid}/timer/start")
async def start_timer2(cid: str, employee_id: Optional[str] = None, u=Depends(get_current_user)):
    tid = f"tmr-{uuid.uuid4().hex[:8]}"
    ACTIVE_TIMERS[cid] = {"started_at": time.time(), "employee_id": employee_id or u["id"], "timer_id": tid}
    return {"card_id": cid, "started_at": datetime.now().isoformat(), "timerId": tid}


@router.post("/cards/{cid}/timer/stop")
async def stop_timer2(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await stop_timer(cid, u, db)


@router.post("/cards/{cid}/comments")
async def add_comment(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await db.get(KanbanCardModel, cid)
    if not card:
        raise HTTPException(404)

    comment = CardCommentModel(
        id=f"cmt-{uuid.uuid4().hex[:6]}",
        card_id=cid,
        author=u["full_name"],
        content=d.get("content"),
        created_at=datetime.now().isoformat(),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return model_to_dict(comment)
