from __future__ import annotations

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.calendar import lima_day_bounds
from app.domain.cci import build_cci
from app.infrastructure import mappers
from app.infrastructure.models import (
    AccountModel,
    BeneficiaryModel,
    CardModel,
    MovementModel,
    PaymentModel,
    RefreshTokenModel,
    TransferModel,
    UserModel,
)
from app.types.entities import Account, Beneficiary, Card, Movement, Payment, RefreshToken, Transfer, User


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: str) -> User | None:
        model = self.session.get(UserModel, user_id)
        return mappers.user_from(model) if model else None

    def get_for_update(self, user_id: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.id == user_id).with_for_update())
        return mappers.user_from(model) if model else None

    def get_by_dni(self, dni: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.dni == dni))
        return mappers.user_from(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email.lower()))
        return mappers.user_from(model) if model else None

    def add(self, user: User) -> None:
        self.session.add(mappers.user_to(user))

    def update(self, user: User) -> None:
        model = self.session.get(UserModel, user.id)
        if model is None:
            raise LookupError(user.id)
        mappers.copy_user(model, user)


class SqlAccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(self, user_id: str) -> list[Account]:
        rows = self.session.scalars(
            select(AccountModel).where(AccountModel.user_id == user_id).order_by(AccountModel.opened_on)
        ).all()
        return [mappers.account_from(row) for row in rows]

    def get(self, account_id: str) -> Account | None:
        model = self.session.get(AccountModel, account_id)
        return mappers.account_from(model) if model else None

    def get_by_number(self, number: str) -> Account | None:
        model = self.session.scalar(select(AccountModel).where(AccountModel.number == number))
        return mappers.account_from(model) if model else None

    def get_by_cci(self, cci: str) -> Account | None:
        model = self.session.scalar(select(AccountModel).where(AccountModel.cci == cci))
        return mappers.account_from(model) if model else None

    def get_for_update(self, account_id: str) -> Account | None:
        model = self.session.scalar(
            select(AccountModel).where(AccountModel.id == account_id).with_for_update()
        )
        return mappers.account_from(model) if model else None

    def get_by_number_for_update(self, number: str) -> Account | None:
        model = self.session.scalar(
            select(AccountModel).where(AccountModel.number == number).with_for_update()
        )
        return mappers.account_from(model) if model else None

    def get_by_cci_for_update(self, cci: str) -> Account | None:
        model = self.session.scalar(
            select(AccountModel).where(AccountModel.cci == cci).with_for_update()
        )
        return mappers.account_from(model) if model else None

    def add(self, account: Account) -> None:
        self.session.add(mappers.account_to(account))

    def save(self, account: Account) -> None:
        model = self.session.get(AccountModel, account.id)
        if model is None:
            raise LookupError(account.id)
        model.available_balance = account.available_balance
        model.status = account.status
        model.alias = account.alias

    def next_number(self) -> str:
        for _ in range(20):
            candidate = "001" + f"{secrets.randbelow(10**11):011d}"
            exists = self.session.scalar(select(AccountModel.id).where(AccountModel.number == candidate))
            if exists is None:
                return candidate
        raise RuntimeError("No se pudo asignar un número de cuenta.")


class SqlMovementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, movement: Movement) -> None:
        self.session.add(mappers.movement_to(movement))

    def list_by_account(self, account_id: str, page: int, page_size: int) -> tuple[list[Movement], int]:
        base = select(MovementModel).where(MovementModel.account_id == account_id)
        total = self.session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self.session.scalars(
            base.order_by(MovementModel.occurred_at.desc(), MovementModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return [mappers.movement_from(row) for row in rows], int(total)


class SqlTransferRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, transfer: Transfer) -> None:
        self.session.add(mappers.transfer_to(transfer))

    def get(self, transfer_id: str) -> Transfer | None:
        model = self.session.get(TransferModel, transfer_id)
        return mappers.transfer_from(model) if model else None

    def sum_amount_on(self, user_id: str, day) -> object:
        start, end = lima_day_bounds(day)
        total = self.session.scalar(
            select(func.coalesce(func.sum(TransferModel.amount), 0)).where(
                TransferModel.user_id == user_id,
                TransferModel.created_at >= start,
                TransferModel.created_at < end,
            )
        )
        return total


class SqlPaymentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, payment: Payment) -> None:
        self.session.add(mappers.payment_to(payment))

    def list_by_user(self, user_id: str, page: int, page_size: int) -> tuple[list[Payment], int]:
        base = select(PaymentModel).where(PaymentModel.user_id == user_id)
        total = self.session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self.session.scalars(
            base.order_by(PaymentModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return [mappers.payment_from(row) for row in rows], int(total)


class SqlCardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(self, user_id: str) -> list[Card]:
        rows = self.session.scalars(select(CardModel).where(CardModel.user_id == user_id)).all()
        return [mappers.card_from(row) for row in rows]

    def get(self, card_id: str) -> Card | None:
        model = self.session.get(CardModel, card_id)
        return mappers.card_from(model) if model else None

    def add(self, card: Card) -> None:
        self.session.add(mappers.card_to(card))

    def save(self, card: Card) -> None:
        model = self.session.get(CardModel, card.id)
        if model is None:
            raise LookupError(card.id)
        model.status = card.status


class SqlBeneficiaryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_user(self, user_id: str) -> list[Beneficiary]:
        rows = self.session.scalars(
            select(BeneficiaryModel)
            .where(BeneficiaryModel.user_id == user_id)
            .order_by(BeneficiaryModel.alias)
        ).all()
        return [mappers.beneficiary_from(row) for row in rows]

    def get(self, beneficiary_id: str) -> Beneficiary | None:
        model = self.session.get(BeneficiaryModel, beneficiary_id)
        return mappers.beneficiary_from(model) if model else None

    def add(self, beneficiary: Beneficiary) -> None:
        self.session.add(mappers.beneficiary_to(beneficiary))

    def delete(self, beneficiary_id: str, user_id: str) -> bool:
        model = self.session.get(BeneficiaryModel, beneficiary_id)
        if model is None or model.user_id != user_id:
            return False
        self.session.delete(model)
        return True


class SqlTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, token: RefreshToken) -> None:
        self.session.add(mappers.token_to(token))

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        model = self.session.scalar(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        return mappers.token_from(model) if model else None

    def save(self, token: RefreshToken) -> None:
        model = self.session.get(RefreshTokenModel, token.id)
        if model is None:
            raise LookupError(token.id)
        model.revoked = token.revoked
        model.expires_at = token.expires_at

    def revoke_all(self, user_id: str) -> None:
        rows = self.session.scalars(
            select(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked.is_(False),
            )
        ).all()
        for row in rows:
            row.revoked = True


def cci_for(number: str) -> str:
    return build_cci(number)
