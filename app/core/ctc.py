# NOTA: Calcula o CTC (custo total do colaborador) e o custo por hora a partir do salário, do tipo de contrato e dos multiplicadores da empresa.

"""Employee total cost (CTC) from the company's own parameters (CFG-1)."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CtcParamsModel
from app.core.money import decimal_value, money

DEFAULTS = {"clt_multiplier": 1.75, "pj_multiplier": 1.10, "estagio_multiplier": 1.10, "monthly_hours": 176.0}


async def get_params(db: AsyncSession, company_id: str) -> CtcParamsModel:
    params = await db.get(CtcParamsModel, company_id)
    if params is None:
        params = CtcParamsModel(company_id=company_id, **DEFAULTS)
        db.add(params)
        await db.flush()
    return params


def compute(base_salary: float, contract_type: Optional[str], params: CtcParamsModel) -> tuple[float, float]:
    multiplier = {
        "CLT": params.clt_multiplier,
        "ESTAGIO": params.estagio_multiplier,
    }.get(contract_type or "", params.pj_multiplier)
    ctc = money(decimal_value(base_salary or 0) * decimal_value(multiplier))
    return ctc, money(ctc / decimal_value(params.monthly_hours))
