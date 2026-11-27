from __future__ import annotations

from app.domain.cci import cci_checksum_ok, cci_is_ours
from app.domain.errors import DomainError
from app.domain.ids import new_id
from app.domain.validators import account_number_error, cci_shape_error, clean_spaces, concept_error, name_error, require
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import Beneficiary, BeneficiaryCommand, Card
from app.types.ports import Clock

MAX_BENEFICIARIES = 20


class CardService:
    def list_for(self, uow: SqlUnitOfWork, user_id: str) -> list[Card]:
        return uow.cards.list_by_user(user_id)

    def set_blocked(self, uow: SqlUnitOfWork, user_id: str, card_id: str, blocked: bool) -> Card:
        card = uow.cards.get(card_id)
        if card is None or card.user_id != user_id:
            raise DomainError("NOT_FOUND", "La tarjeta no existe.")
        target = "blocked" if blocked else "active"
        if card.status == target:
            state = "bloqueada" if blocked else "activa"
            raise DomainError("CONFLICT", f"La tarjeta ya está {state}.")
        card.status = target  # type: ignore[assignment]
        uow.cards.save(card)
        return card


class BeneficiaryService:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def list_for(self, uow: SqlUnitOfWork, user_id: str) -> list[Beneficiary]:
        return uow.beneficiaries.list_by_user(user_id)

    def add(self, uow: SqlUnitOfWork, user_id: str, command: BeneficiaryCommand) -> Beneficiary:
        if len(uow.beneficiaries.list_by_user(user_id)) >= MAX_BENEFICIARIES:
            raise DomainError("LIMIT_EXCEEDED", "El directorio admite 20 beneficiarios.")
        holder = clean_spaces(command.holder_name or "")
        alias = clean_spaces(command.alias or "")
        bank = clean_spaces(command.bank_name or "")
        number = (command.account_number or "").strip() or None
        cci = (command.cci or "").strip() or None
        errors = [
            item
            for item in (
                name_error(holder, "El titular"),
                concept_error(alias, "El alias", 40),
                concept_error(bank, "El banco", 80),
            )
            if item
        ]
        if (number is None) == (cci is None):
            errors.append("Indique la cuenta de AndesBank o el CCI, no los dos.")
        if number is not None:
            problem = account_number_error(number)
            if problem:
                errors.append(problem)
        if cci is not None:
            problem = cci_shape_error(cci)
            if problem:
                errors.append(problem)
            elif cci_is_ours(cci) and not cci_checksum_ok(cci):
                errors.append("El CCI no supera el dígito de control de AndesBank.")
        require(errors)
        if number is not None and uow.accounts.get_by_number(number) is None:
            raise DomainError("NOT_FOUND", "Esa cuenta de AndesBank no existe.")
        item = Beneficiary(
            id=new_id(),
            user_id=user_id,
            holder_name=holder,
            alias=alias,
            bank_name=bank,
            account_number=number,
            cci=cci,
            created_at=self.clock.now(),
        )
        uow.beneficiaries.add(item)
        return item

    def delete(self, uow: SqlUnitOfWork, user_id: str, beneficiary_id: str) -> None:
        if not uow.beneficiaries.delete(beneficiary_id, user_id):
            raise DomainError("NOT_FOUND", "El beneficiario no existe.")
