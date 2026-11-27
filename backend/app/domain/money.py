from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")
MONEY_QUANTUM = CENT


def money(value: Decimal | int | str) -> Decimal:
    try:
        amount = Decimal(value) if not isinstance(value, Decimal) else value
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("monto ilegible") from exc
    if amount != amount.quantize(CENT):
        raise ValueError("el monto admite como máximo dos decimales")
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def money_str(value: Decimal) -> str:
    return f"{money(value):.2f}"


def parse_amount(raw: str) -> Decimal:
    """Acepta ``1500``, ``1500.5`` y ``1500.50``.

    Rechaza separadores de miles, coma decimal, notación científica y signo.
    El redondeo silencioso esconde errores de captura: si hay más de dos
    decimales, la operación no entra.
    """
    if not isinstance(raw, str) or raw != raw.strip() or not raw:
        raise ValueError("El monto debe escribirse con punto decimal y sin separador de miles.")
    text = raw
    if any(ch in text for ch in "eE+-, "):
        raise ValueError("El monto debe escribirse con punto decimal y sin separador de miles.")
    if text.startswith("."):
        raise ValueError("El monto debe escribirse con punto decimal y sin separador de miles.")
    whole, dot, fraction = text.partition(".")
    if not whole.isdigit() or (whole.startswith("0") and whole != "0"):
        raise ValueError("El monto debe escribirse con punto decimal y sin separador de miles.")
    if dot and (not fraction.isdigit() or len(fraction) > 2):
        raise ValueError("El monto admite como máximo dos decimales.")
    return money(text)
