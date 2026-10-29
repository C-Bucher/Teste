"""Decimal arithmetic shared by persistence and financial workflows."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def decimal_value(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Valor monetário inválido") from None
    if not result.is_finite():
        raise ValueError("Valor monetário deve ser finito")
    return result


def money(value, places: int = 2) -> Decimal:
    value = decimal_value(value)
    try:
        value = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("Valor monetário fora do limite") from None
    if abs(value) >= Decimal(10) ** (14 - places):
        raise ValueError("Valor monetário fora do limite")
    return value


def money_input(value, places: int = 2) -> Decimal:
    from fastapi import HTTPException

    try:
        return money(value, places)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
