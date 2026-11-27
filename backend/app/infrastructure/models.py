from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dni: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(9))
    given_names: Mapped[str] = mapped_column(String(80))
    paternal_surname: Mapped[str] = mapped_column(String(80))
    maternal_surname: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(200))
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    product_type: Mapped[str] = mapped_column(String(20))
    number: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    cci: Mapped[str] = mapped_column(String(20), unique=True)
    currency: Mapped[str] = mapped_column(String(3), default="PEN")
    available_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(20), default="active")
    alias: Mapped[str] = mapped_column(String(40))
    opened_on: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MovementModel(Base):
    __tablename__ = "movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), index=True)
    direction: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    concept: Mapped[str] = mapped_column(String(120))
    counterparty_name: Mapped[str] = mapped_column(String(120), default="")
    counterparty_account: Mapped[str] = mapped_column(String(20), default="")
    channel: Mapped[str] = mapped_column(String(30))
    operation_code: Mapped[str] = mapped_column(String(24), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    transfer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class TransferModel(Base):
    __tablename__ = "transfers"
    __table_args__ = (UniqueConstraint("operation_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    origin_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    destination_account_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    destination_number: Mapped[str] = mapped_column(String(20))
    destination_holder: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    commission: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    concept: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    operation_code: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("operation_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    service_code: Mapped[str] = mapped_column(String(30))
    service_name: Mapped[str] = mapped_column(String(80))
    reference: Mapped[str] = mapped_column(String(40))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    operation_code: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CardModel(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    brand: Mapped[str] = mapped_column(String(20))
    last4: Mapped[str] = mapped_column(String(4))
    holder_name: Mapped[str] = mapped_column(String(80))
    expiry_month: Mapped[int] = mapped_column(Integer)
    expiry_year: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)


class BeneficiaryModel(Base):
    __tablename__ = "beneficiaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    holder_name: Mapped[str] = mapped_column(String(120))
    alias: Mapped[str] = mapped_column(String(40))
    bank_name: Mapped[str] = mapped_column(String(80))
    account_number: Mapped[str | None] = mapped_column(String(14), nullable=True)
    cci: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
