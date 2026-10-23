# NOTA: Converte um registro do banco em dicionário, no formato que o front espera.

def model_to_dict(obj) -> dict:
    """Converts a SQLAlchemy ORM instance to a plain dict matching the
    same field names/shape the old in-memory mock dicts used, so every
    router's response format stays identical after the DB migration."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def models_to_dicts(objs) -> list[dict]:
    return [model_to_dict(o) for o in objs]
