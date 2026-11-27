from __future__ import annotations

from decimal import Decimal

from app.domain.calendar import lima_day
from app.domain.cci import cci_checksum_ok, cci_is_ours
from app.domain.errors import DomainError
from app.domain.ids import new_id, operation_code
from app.domain.money import money, parse_amount
from app.domain.policies import (
    MAX_TRANSFER,
    assert_amount_bounds,
    assert_can_debit,
    assert_daily_limit,
    assert_destination_operable,
    commission_for,
    needs_step_up,
)
from app.domain.validators import (
    account_number_error,
    cci_shape_error,
    clean_spaces,
    concept_error,
    name_error,
    require,
)
from app.infrastructure.security import totp_matches
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import Account, Movement, Transfer, TransferCommand, User
from app.types.ports import Clock


class TransferService:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def create(self, uow: SqlUnitOfWork, user_id: str, command: TransferCommand) -> Transfer:
        user = uow.users.get_for_update(user_id)
        if user is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        if user.status != "active":
            raise DomainError("USER_BLOCKED", "El usuario no puede operar. La revisión se hace en una agencia.")
        amount, concept, destination = self._validated(command)
        origin_id, dest_id, kind, number, holder = self._resolve(uow, user_id, command, destination)
        self._step_up(user, amount, command.otp_code)
        locked = self._lock(uow, origin_id, dest_id)
        origin = locked[origin_id]
        dest = locked.get(dest_id) if dest_id else None
        if origin is None or origin.user_id != user_id:
            raise DomainError("NOT_FOUND", "La cuenta de origen no existe.")
        if kind == "internal":
            if dest is None:
                raise DomainError("NOT_FOUND", "La cuenta de destino no existe.")
            assert_destination_operable(dest, origin)
            owner = uow.users.get_by_id(dest.user_id)
            if owner is None or owner.status != "active":
                raise DomainError("DEST_UNAVAILABLE", "La cuenta de destino no está operativa.")
            holder = owner.full_name
            number = dest.cci if destination == "cci" else dest.number
        commission = commission_for(kind)
        assert_can_debit(origin, money(amount + commission))
        already = money(Decimal(str(uow.transfers.sum_amount_on(user.id, lima_day(self.clock.now())))))
        assert_daily_limit(already, amount)
        return self._post(uow, user, origin, dest, amount, commission, concept, kind, number, holder)

    def get(self, uow: SqlUnitOfWork, user_id: str, transfer_id: str) -> Transfer:
        found = uow.transfers.get(transfer_id)
        if found is None or found.user_id != user_id:
            raise DomainError("NOT_FOUND", "La transferencia no existe.")
        return found

    def _validated(self, command: TransferCommand) -> tuple[Decimal, str, str]:
        errors: list[str] = []
        concept = clean_spaces(command.concept or "")
        concept_problem = concept_error(concept)
        if concept_problem:
            errors.append(concept_problem)
        has_number = bool((command.destination_account_number or "").strip())
        has_cci = bool((command.destination_cci or "").strip())
        if has_number == has_cci:
            errors.append("Indique el número de cuenta de 14 dígitos o el CCI de 20, no los dos.")
        if has_number:
            problem = account_number_error(command.destination_account_number or "")
            if problem:
                errors.append(problem)
        if has_cci:
            problem = cci_shape_error(command.destination_cci or "")
            if problem:
                errors.append(problem)
        amount: Decimal | None = None
        try:
            amount = parse_amount(command.amount)
        except ValueError as exc:
            errors.append(str(exc))
        require(errors)
        assert amount is not None
        assert_amount_bounds(amount, MAX_TRANSFER, "una transferencia")
        return amount, concept, "account" if has_number else "cci"

    def _resolve(
        self,
        uow: SqlUnitOfWork,
        user_id: str,
        command: TransferCommand,
        destination: str,
    ) -> tuple[str, str | None, str, str, str]:
        origin = uow.accounts.get(command.origin_account_id)
        if origin is None or origin.user_id != user_id:
            raise DomainError("NOT_FOUND", "La cuenta de origen no existe.")
        if destination == "account":
            number = (command.destination_account_number or "").strip()
            dest = uow.accounts.get_by_number(number)
            if dest is None:
                raise DomainError("NOT_FOUND", "La cuenta de destino no existe.")
            return origin.id, dest.id, "internal", number, ""
        cci = (command.destination_cci or "").strip()
        if cci_is_ours(cci):
            if not cci_checksum_ok(cci):
                raise DomainError("CCI_INVALID", "El CCI no supera el dígito de control de AndesBank.")
            dest = uow.accounts.get_by_cci(cci)
            if dest is None:
                raise DomainError("NOT_FOUND", "La cuenta de destino no existe.")
            return origin.id, dest.id, "internal", cci, ""
        holder = clean_spaces(command.destination_holder or "")
        problem = name_error(holder, "El titular")
        if problem:
            raise DomainError("VALIDATION", "Hay datos que no pasan la validación.", [problem])
        return origin.id, None, "external", cci, holder

    def _step_up(self, user: User, amount: Decimal, otp_code: str | None) -> None:
        if not needs_step_up(user.totp_enabled, amount):
            return
        if not otp_code:
            raise DomainError(
                "OTP_REQUIRED",
                "Esta operación pide el código de 6 dígitos del autenticador.",
            )
        if not user.totp_secret or not totp_matches(user.totp_secret, otp_code, self.clock.now()):
            raise DomainError("OTP_INVALID", "El código del autenticador no coincide.")

    def _lock(self, uow: SqlUnitOfWork, origin_id: str, dest_id: str | None) -> dict[str, Account | None]:
        locked: dict[str, Account | None] = {}
        for account_id in sorted({origin_id, dest_id} - {None}):
            locked[account_id] = uow.accounts.get_for_update(account_id)  # type: ignore[index]
        return locked

    def _post(
        self,
        uow: SqlUnitOfWork,
        user: User,
        origin: Account,
        dest: Account | None,
        amount: Decimal,
        commission: Decimal,
        concept: str,
        kind: str,
        number: str,
        holder: str,
    ) -> Transfer:
        now = self.clock.now()
        code = operation_code(now)
        transfer = Transfer(
            id=new_id(),
            user_id=user.id,
            origin_account_id=origin.id,
            destination_account_id=dest.id if dest else None,
            destination_number=number,
            destination_holder=holder,
            amount=amount,
            commission=commission,
            concept=concept,
            kind=kind,  # type: ignore[arg-type]
            status="completada" if kind == "internal" else "enviada",
            operation_code=code,
            created_at=now,
        )
        after_amount = money(origin.available_balance - amount)
        after_all = money(after_amount - commission)
        origin.available_balance = after_all
        uow.accounts.save(origin)
        uow.transfers.add(transfer)
        uow.movements.add(
            self._line(origin.id, "debit", amount, after_amount, concept, holder, number, "transferencia", code, now, transfer.id)
        )
        if commission > 0:
            uow.movements.add(
                self._line(
                    origin.id,
                    "debit",
                    commission,
                    after_all,
                    "Comisión transferencia interbancaria",
                    "AndesBank",
                    "",
                    "comision",
                    code,
                    now,
                    transfer.id,
                )
            )
        if dest is not None:
            credited = money(dest.available_balance + amount)
            dest.available_balance = credited
            uow.accounts.save(dest)
            uow.movements.add(
                self._line(
                    dest.id,
                    "credit",
                    amount,
                    credited,
                    concept,
                    user.full_name,
                    origin.number,
                    "transferencia",
                    code,
                    now,
                    transfer.id,
                )
            )
        return transfer

    def _line(
        self,
        account_id: str,
        direction: str,
        amount: Decimal,
        balance_after: Decimal,
        concept: str,
        counterparty: str,
        counterparty_account: str,
        channel: str,
        code: str,
        occurred_at,
        transfer_id: str,
    ) -> Movement:
        return Movement(
            id=new_id(),
            account_id=account_id,
            direction=direction,  # type: ignore[arg-type]
            amount=amount,
            balance_after=balance_after,
            concept=concept,
            counterparty_name=counterparty,
            counterparty_account=counterparty_account,
            channel=channel,
            operation_code=code,
            occurred_at=occurred_at,
            transfer_id=transfer_id,
        )
