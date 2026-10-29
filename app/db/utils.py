# NOTA: Converte um registro do banco em dicionário, no formato que o front espera.

def normalize_money_fields(model, data: dict) -> dict:
    """Normalize money at write boundaries; preserve Decimal until JSON output."""
    from sqlalchemy import Numeric
    from app.core.money import money_input

    result = dict(data)
    for column in model.__table__.columns:
        if isinstance(column.type, Numeric) and result.get(column.name) is not None:
            result[column.name] = money_input(result[column.name], column.type.scale)
    return result

def model_to_dict(obj) -> dict:
    """Converts a SQLAlchemy ORM instance to a plain dict matching the
    same field names/shape the old in-memory mock dicts used, so every
    router's response format stays identical after the DB migration."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def models_to_dicts(objs) -> list[dict]:
    return [model_to_dict(o) for o in objs]
