from __future__ import annotations

from decimal import Decimal

from app.domain.errors import DomainError
from app.domain.money import money
from app.types.entities import Account

MIN_OPERATION = money("1.00")
MAX_TRANSFER = money("10000.00")
MAX_PAYMENT = money("5000.00")
DAILY_LIMIT = money("20000.00")
EXTERNAL_COMMISSION = money("4.50")
OTP_STEP_UP = money("500.00")
LOGIN_LOCK_ATTEMPTS = 5
LOCK_MINUTES = 15


def product_label(product_type: str) -> str:
    labels = {
        "ahorro": "Cuenta de ahorros",
        "corriente": "Cuenta corriente",
        "cts": "CTS",
    }
    try:
        return labels[product_type]
    except KeyError as exc:
        raise DomainError("VALIDATION", "El producto no existe.", []) from exc


def assert_can_debit(account: Account, total: Decimal) -> None:
    if account.product_type == "cts":
        raise DomainError(
            "CTS_RESTRICTED",
            "La CTS no admite cargos desde la aplicación. El retiro se atiende en agencia, con la documentación del empleador.",
        )
    if account.status != "active":
        raise DomainError("ACCOUNT_BLOCKED", "La cuenta de origen no está operativa.")
    if account.currency != "PEN":
        raise DomainError("CURRENCY", "Esta versión solo opera en soles.")
    if total > account.available_balance:
        raise DomainError(
            "INSUFFICIENT_FUNDS",
            "El saldo disponible no cubre el monto y la comisión.",
        )


def assert_amount_bounds(amount: Decimal, ceiling: Decimal, label: str) -> None:
    if amount < MIN_OPERATION:
        raise DomainError("AMOUNT_TOO_SMALL", f"El mínimo de {label} es S/ {MIN_OPERATION:.2f}.")
    if amount > ceiling:
        raise DomainError("LIMIT_EXCEEDED", f"El máximo por operación de {label} es S/ {ceiling:.2f}.")


def assert_daily_limit(already: Decimal, amount: Decimal) -> None:
    if already + amount > DAILY_LIMIT:
        raise DomainError(
            "DAILY_LIMIT",
            "La operación supera el límite diario de S/ 20,000.00.",
        )


def needs_step_up(totp_enabled: bool, amount: Decimal) -> bool:
    return totp_enabled and amount >= OTP_STEP_UP


def commission_for(kind: str) -> Decimal:
    if kind == "external":
        return EXTERNAL_COMMISSION
    if kind == "internal":
        return money("0.00")
    raise DomainError("VALIDATION", "El tipo de transferencia no es válido.")


def assert_destination_operable(account: Account, origin: Account) -> None:
    if account.id == origin.id or account.number == origin.number:
        raise DomainError("SAME_ACCOUNT", "La cuenta de destino es la misma que la de origen.")
    if account.product_type == "cts":
        raise DomainError(
            "CTS_RESTRICTED",
            "No se puede abonar una CTS desde la aplicación.",
        )
    if account.status != "active":
        raise DomainError("DEST_UNAVAILABLE", "La cuenta de destino no está operativa.")
    if account.currency != origin.currency:
        raise DomainError("CURRENCY", "El origen y el destino deben usar la misma moneda.")
