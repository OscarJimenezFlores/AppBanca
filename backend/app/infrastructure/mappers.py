from __future__ import annotations

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


def user_from(model: UserModel) -> User:
    return User(
        id=model.id,
        dni=model.dni,
        email=model.email,
        phone=model.phone,
        given_names=model.given_names,
        paternal_surname=model.paternal_surname,
        maternal_surname=model.maternal_surname,
        password_hash=model.password_hash,
        totp_secret=model.totp_secret,
        totp_enabled=model.totp_enabled,
        status=model.status,  # type: ignore[arg-type]
        failed_attempts=model.failed_attempts,
        locked_until=model.locked_until,
        created_at=model.created_at,
    )


def user_to(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        dni=user.dni,
        email=user.email,
        phone=user.phone,
        given_names=user.given_names,
        paternal_surname=user.paternal_surname,
        maternal_surname=user.maternal_surname,
        password_hash=user.password_hash,
        totp_secret=user.totp_secret,
        totp_enabled=user.totp_enabled,
        status=user.status,
        failed_attempts=user.failed_attempts,
        locked_until=user.locked_until,
        created_at=user.created_at,
    )


def copy_user(model: UserModel, user: User) -> None:
    model.email = user.email
    model.phone = user.phone
    model.password_hash = user.password_hash
    model.totp_secret = user.totp_secret
    model.totp_enabled = user.totp_enabled
    model.status = user.status
    model.failed_attempts = user.failed_attempts
    model.locked_until = user.locked_until


def account_from(model: AccountModel) -> Account:
    return Account(
        id=model.id,
        user_id=model.user_id,
        product_type=model.product_type,  # type: ignore[arg-type]
        number=model.number,
        cci=model.cci,
        currency=model.currency,
        available_balance=model.available_balance,
        status=model.status,  # type: ignore[arg-type]
        alias=model.alias,
        opened_on=model.opened_on,
    )


def account_to(account: Account) -> AccountModel:
    return AccountModel(
        id=account.id,
        user_id=account.user_id,
        product_type=account.product_type,
        number=account.number,
        cci=account.cci,
        currency=account.currency,
        available_balance=account.available_balance,
        status=account.status,
        alias=account.alias,
        opened_on=account.opened_on,
    )


def movement_from(model: MovementModel) -> Movement:
    return Movement(
        id=model.id,
        account_id=model.account_id,
        direction=model.direction,  # type: ignore[arg-type]
        amount=model.amount,
        balance_after=model.balance_after,
        concept=model.concept,
        counterparty_name=model.counterparty_name,
        counterparty_account=model.counterparty_account,
        channel=model.channel,
        operation_code=model.operation_code,
        occurred_at=model.occurred_at,
        transfer_id=model.transfer_id,
        payment_id=model.payment_id,
    )


def movement_to(movement: Movement) -> MovementModel:
    return MovementModel(
        id=movement.id,
        account_id=movement.account_id,
        direction=movement.direction,
        amount=movement.amount,
        balance_after=movement.balance_after,
        concept=movement.concept,
        counterparty_name=movement.counterparty_name,
        counterparty_account=movement.counterparty_account,
        channel=movement.channel,
        operation_code=movement.operation_code,
        occurred_at=movement.occurred_at,
        transfer_id=movement.transfer_id,
        payment_id=movement.payment_id,
    )


def transfer_from(model: TransferModel) -> Transfer:
    return Transfer(
        id=model.id,
        user_id=model.user_id,
        origin_account_id=model.origin_account_id,
        destination_account_id=model.destination_account_id,
        destination_number=model.destination_number,
        destination_holder=model.destination_holder,
        amount=model.amount,
        commission=model.commission,
        concept=model.concept,
        kind=model.kind,  # type: ignore[arg-type]
        status=model.status,  # type: ignore[arg-type]
        operation_code=model.operation_code,
        created_at=model.created_at,
    )


def transfer_to(transfer: Transfer) -> TransferModel:
    return TransferModel(**transfer.__dict__)


def payment_from(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        user_id=model.user_id,
        account_id=model.account_id,
        service_code=model.service_code,
        service_name=model.service_name,
        reference=model.reference,
        amount=model.amount,
        operation_code=model.operation_code,
        created_at=model.created_at,
    )


def payment_to(payment: Payment) -> PaymentModel:
    return PaymentModel(**payment.__dict__)


def card_from(model: CardModel) -> Card:
    return Card(
        id=model.id,
        user_id=model.user_id,
        account_id=model.account_id,
        brand=model.brand,  # type: ignore[arg-type]
        last4=model.last4,
        holder_name=model.holder_name,
        expiry_month=model.expiry_month,
        expiry_year=model.expiry_year,
        status=model.status,  # type: ignore[arg-type]
        is_virtual=model.is_virtual,
    )


def card_to(card: Card) -> CardModel:
    return CardModel(**card.__dict__)


def beneficiary_from(model: BeneficiaryModel) -> Beneficiary:
    return Beneficiary(
        id=model.id,
        user_id=model.user_id,
        holder_name=model.holder_name,
        alias=model.alias,
        bank_name=model.bank_name,
        account_number=model.account_number,
        cci=model.cci,
        created_at=model.created_at,
    )


def beneficiary_to(item: Beneficiary) -> BeneficiaryModel:
    return BeneficiaryModel(**item.__dict__)


def token_from(model: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        expires_at=model.expires_at,
        revoked=model.revoked,
        created_at=model.created_at,
    )


def token_to(token: RefreshToken) -> RefreshTokenModel:
    return RefreshTokenModel(**token.__dict__)
