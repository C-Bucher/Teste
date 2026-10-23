# NOTA: Rotas /kanban: projetos, colunas, cartões (criar, mover, editar, excluir), cronômetro de tempo por cartão,
#       comentários, modelos de projeto e clientes.

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime, timezone

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
    ActiveTimerModel,
)
from app.db.utils import model_to_dict, models_to_dicts

router = APIRouter()

_CLIENT_COLUMNS = {c.name for c in ClientModel.__table__.columns}
_PROJECT_COLUMNS = {c.name for c in ProjectModel.__table__.columns}
_COLUMN_COLUMNS = {c.name for c in KanbanColumnModel.__table__.columns}
_CARD_COLUMNS = {c.name for c in KanbanCardModel.__table__.columns}

# O timer ativo é persistido em ActiveTimerModel; o tempo acumulado permanece no card.
async def _card_for_company(db: AsyncSession, card_id: str, company_id: str) -> KanbanCardModel | None:
    result = await db.execute(
        select(KanbanCardModel)
        .join(KanbanColumnModel, KanbanCardModel.column_id == KanbanColumnModel.id)
        .join(ProjectModel, KanbanColumnModel.project_id == ProjectModel.id)
        .where(KanbanCardModel.id == card_id, ProjectModel.company_id == company_id)
    )
    return result.scalar_one_or_none()


@router.get("/templates")
async def get_kanban_templates(u=Depends(get_current_user)):
    return []


@router.get("/clients")
async def get_clis(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ClientModel).where(ClientModel.company_id == u["company_id"]))
    return models_to_dicts(result.scalars().all())


@router.post("/clients")
async def create_cli(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cli_dict = {**d, "id": f"cli-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"]}
    model_kwargs = {k: v for k, v in cli_dict.items() if k in _CLIENT_COLUMNS}
    cli = ClientModel(**model_kwargs)
    db.add(cli)
    await db.commit()
    await db.refresh(cli)
    return model_to_dict(cli)


@router.put("/clients/{cid}")
async def upd_cli(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cli = await db.get(ClientModel, cid)
    if not cli or cli.company_id != u["company_id"]:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _CLIENT_COLUMNS and k not in {"id", "company_id"}:
            setattr(cli, k, v)
    await db.commit()
    await db.refresh(cli)
    return model_to_dict(cli)


@router.get("/projects")
async def get_projs(client_id: Optional[str] = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(ProjectModel).where(ProjectModel.company_id == u["company_id"])
    if client_id:
        q = q.where(ProjectModel.client_id == client_id)
    result = await db.execute(q)
    return models_to_dicts(result.scalars().all())


@router.post("/projects")
async def create_proj(d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if d.get("client_id"):
        client = await db.get(ClientModel, d["client_id"])
        if not client or client.company_id != u["company_id"]:
            raise HTTPException(404, "Cliente não encontrado")
    proj_dict = {**d, "id": f"proj-{uuid.uuid4().hex[:6]}", "company_id": u["company_id"], "status": "PLANEJAMENTO"}
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
    if not proj or proj.company_id != u["company_id"]:
        raise HTTPException(404, "Projeto não encontrado")
    cli = await db.get(ClientModel, proj.client_id) if proj and proj.client_id else None

    columns_result = await db.execute(
        select(KanbanColumnModel).where(KanbanColumnModel.project_id == pid).order_by(KanbanColumnModel.order)
    )
    columns = columns_result.scalars().all()
    column_ids = [col.id for col in columns]

    # Three queries for the whole board instead of one per column and one per card (DB-4).
    cards = (await db.execute(select(KanbanCardModel).where(KanbanCardModel.column_id.in_(column_ids)))).scalars().all() if column_ids else []
    card_ids = [card.id for card in cards]
    comments = (await db.execute(
        select(CardCommentModel).where(CardCommentModel.card_id.in_(card_ids)).order_by(CardCommentModel.created_at)
    )).scalars().all() if card_ids else []

    comments_by_card: dict[str, list] = {}
    for comment in comments:
        comments_by_card.setdefault(comment.card_id, []).append(model_to_dict(comment))
    cards_by_column: dict[str, list] = {}
    for card in cards:
        card_dict = model_to_dict(card)
        card_dict["comments"] = comments_by_card.get(card.id, [])
        cards_by_column.setdefault(card.column_id, []).append(card_dict)

    columns_out = []
    for col in columns:
        col_dict = model_to_dict(col)
        col_dict["cards"] = cards_by_column.get(col.id, [])
        columns_out.append(col_dict)

    return {
        "project": model_to_dict(proj) if proj else None,
        "client": model_to_dict(cli) if cli else None,
        "columns": columns_out,
    }


@router.post("/projects/{pid}/columns")
async def add_col(pid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await db.get(ProjectModel, pid)
    if not project or project.company_id != u["company_id"]:
        raise HTTPException(404, "Projeto não encontrado")
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
    project = await db.get(ProjectModel, col.project_id) if col else None
    if not col or not project or project.company_id != u["company_id"]:
        raise HTTPException(404, "Coluna nao encontrada")
    if d.get("assignee_id"):
        employee = await db.get(EmployeeModel, d["assignee_id"])
        if not employee or employee.company_id != u["company_id"]:
            raise HTTPException(404, "Colaborador não encontrado")

    card_dict = {
        **d,
        "id": f"card-{uuid.uuid4().hex[:6]}",
        "cost_per_task": 0,
        "total_time_seconds": 0,
        "status": "ABERTO",
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
    card = await _card_for_company(db, cid, u["company_id"])
    if not card:
        raise HTTPException(404)

    new_col = d.get("column_id")
    if new_col:
        col = await db.get(KanbanColumnModel, new_col)
        project = await db.get(ProjectModel, col.project_id) if col else None
        if not col or not project or project.company_id != u["company_id"]:
            raise HTTPException(404, "Coluna de destino nao encontrada")
        card.column_id = new_col
        await db.commit()

    return {"id": cid, "column_id": new_col, "moved": True}


@router.put("/cards/{cid}")
async def upd_card(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await _card_for_company(db, cid, u["company_id"])
    if not card:
        raise HTTPException(404)
    for k, v in d.items():
        if k in _CARD_COLUMNS and k not in {"id", "column_id"}:
            setattr(card, k, v)
    await db.commit()
    await db.refresh(card)
    return model_to_dict(card)


@router.delete("/cards/{cid}")
async def del_card(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await _card_for_company(db, cid, u["company_id"])
    if not card:
        raise HTTPException(404)
    comments_result = await db.execute(select(CardCommentModel).where(CardCommentModel.card_id == cid))
    for comment in comments_result.scalars().all():
        await db.delete(comment)
    timer = await db.get(ActiveTimerModel, cid)
    if timer:
        await db.delete(timer)
    await db.delete(card)
    await db.commit()
    return {"success": True}


@router.post("/cards/{cid}/time/start")
async def start_timer(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await _card_for_company(db, cid, u["company_id"])
    if not card:
        raise HTTPException(404)
    if await db.get(ActiveTimerModel, cid):
        raise HTTPException(409, "Já existe um timer ativo para este cartão")
    started_at = datetime.now(timezone.utc).isoformat()
    timer = ActiveTimerModel(card_id=cid, started_at=started_at, employee_id=card.assignee_id or u["id"], timer_id=f"tmr-{uuid.uuid4().hex[:8]}")
    db.add(timer)
    await db.commit()
    return {"card_id": cid, "started_at": started_at, "timerId": timer.timer_id}


@router.post("/cards/{cid}/time/stop")
async def stop_timer(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await _card_for_company(db, cid, u["company_id"])
    if not card:
        raise HTTPException(404)
    timer = await db.get(ActiveTimerModel, cid)
    if not timer:
        raise HTTPException(409, "Nenhum timer ativo para este cartão")
    elapsed = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(timer.started_at)).total_seconds()))
    card.total_time_seconds = (card.total_time_seconds or 0) + elapsed
    emp = await db.get(EmployeeModel, card.assignee_id) if card.assignee_id else None
    if emp and emp.company_id != u["company_id"]:
        emp = None
    rate = emp.hourly_rate if emp and emp.hourly_rate else 85
    card.cost_per_task = round(card.total_time_seconds / 3600 * rate, 2)
    await db.delete(timer)
    await db.commit()
    return {"card_id": cid, "elapsed_seconds": elapsed, "total_time_seconds": card.total_time_seconds, "cost_per_task": card.cost_per_task}


@router.post("/cards/{cid}/timer/start")
async def start_timer2(cid: str, employee_id: Optional[str] = None, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await start_timer(cid, u, db)


@router.post("/cards/{cid}/timer/stop")
async def stop_timer2(cid: str, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await stop_timer(cid, u, db)


@router.post("/cards/{cid}/comments")
async def add_comment(cid: str, d: dict, u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    card = await _card_for_company(db, cid, u["company_id"])
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
