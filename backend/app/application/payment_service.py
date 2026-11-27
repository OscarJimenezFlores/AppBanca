from __future__ import annotations

import re
from decimal import Decimal

from app.domain.catalog import service_amount_ok, service_by_code
from app.domain.errors import DomainError
from app.domain.ids import new_id, operation_code
from app.domain.money import money, parse_amount
from app.domain.policies import needs_step_up
from app.domain.policies import assert_can_debit
from app.domain.validators import require
from app.infrastructure.security import totp_matches
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import Movement, Payment, PaymentCommand
from app.types.ports import Clock


class PaymentService:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def pay(self, uow: SqlUnitOfWork, user_id: str, command: PaymentCommand) -> Payment:
        user = uow.users.get_for_update(user_id)
        if user is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        if user.status != "active":
            raise DomainError("USER_BLOCKED", "El usuario no puede operar. La revisión se hace en una agencia.")
        service = service_by_code((command.service_code or "").strip().upper())
        reference = (command.reference or "").strip()
        errors: list[str] = []
        if service is None:
            errors.append("El servicio no está en el catálogo.")
        elif not re.fullmatch(service.reference_pattern, reference):
            errors.append(f"{service.reference_label} no tiene el formato que exige {service.name}.")
        try:
            amount = parse_amount(command.amount)
        except ValueError as exc:
            errors.append(str(exc))
            amount = None
        require(errors)
        assert service is not None and amount is not None
        problem = service_amount_ok(service, amount)
        if problem:
            raise DomainError("LIMIT_EXCEEDED", problem)
        if needs_step_up(user.totp_enabled, amount):
            if not command.otp_code:
                raise DomainError("OTP_REQUIRED", "Esta operación pide el código de 6 dígitos del autenticador.")
            if not user.totp_secret or not totp_matches(user.totp_secret, command.otp_code, self.clock.now()):
                raise DomainError("OTP_INVALID", "El código del autenticador no coincide.")
        origin = uow.accounts.get_for_update(command.origin_account_id)
        if origin is None or origin.user_id != user_id:
            raise DomainError("NOT_FOUND", "La cuenta de origen no existe.")
        assert_can_debit(origin, amount)
        now = self.clock.now()
        code = operation_code(now)
        payment = Payment(
            id=new_id(),
            user_id=user.id,
            account_id=origin.id,
            service_code=service.code,
            service_name=service.name,
            reference=reference,
            amount=amount,
            operation_code=code,
            created_at=now,
        )
        after = money(origin.available_balance - amount)
        origin.available_balance = after
        uow.accounts.save(origin)
        uow.payments.add(payment)
        uow.movements.add(
            Movement(
                id=new_id(),
                account_id=origin.id,
                direction="debit",
                amount=amount,
                balance_after=after,
                concept=f"Pago {service.name}",
                counterparty_name=service.name,
                counterparty_account=reference,
                channel="pago_servicio",
                operation_code=code,
                occurred_at=now,
                payment_id=payment.id,
            )
        )
        return payment

    def list_for(self, uow: SqlUnitOfWork, user_id: str, page: int, page_size: int) -> tuple[list[Payment], int]:
        return uow.payments.list_by_user(user_id, page, page_size)
