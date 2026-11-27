from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal

ProductType = Literal["ahorro", "corriente", "cts"]
AccountStatus = Literal["active", "blocked"]
UserStatus = Literal["active", "blocked"]
MovementDirection = Literal["credit", "debit"]
TransferKind = Literal["internal", "external"]
TransferStatus = Literal["completada", "enviada"]
CardBrand = Literal["visa", "mastercard"]
CardStatus = Literal["active", "blocked"]
BranchKind = Literal["agencia", "cajero"]


@dataclass
class User:
    id: str
    dni: str
    email: str
    phone: str
    given_names: str
    paternal_surname: str
    maternal_surname: str
    password_hash: str
    totp_secret: str | None
    totp_enabled: bool
    status: UserStatus
    failed_attempts: int
    locked_until: datetime | None
    created_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.given_names} {self.paternal_surname} {self.maternal_surname}".strip()


@dataclass
class Account:
    id: str
    user_id: str
    product_type: ProductType
    number: str
    cci: str
    currency: str
    available_balance: Decimal
    status: AccountStatus
    alias: str
    opened_on: datetime


@dataclass(frozen=True)
class StoryLine:
    occurred_at: datetime
    direction: MovementDirection
    amount: Decimal
    concept: str
    counterparty_name: str
    counterparty_account: str
    channel: str


@dataclass(frozen=True)
class PostedLine:
    occurred_at: datetime
    direction: MovementDirection
    amount: Decimal
    concept: str
    counterparty_name: str
    counterparty_account: str
    channel: str
    balance_after: Decimal


@dataclass
class Movement:
    id: str
    account_id: str
    direction: MovementDirection
    amount: Decimal
    balance_after: Decimal
    concept: str
    counterparty_name: str
    counterparty_account: str
    channel: str
    operation_code: str
    occurred_at: datetime
    transfer_id: str | None = None
    payment_id: str | None = None


@dataclass
class Transfer:
    id: str
    user_id: str
    origin_account_id: str
    destination_account_id: str | None
    destination_number: str
    destination_holder: str
    amount: Decimal
    commission: Decimal
    concept: str
    kind: TransferKind
    status: TransferStatus
    operation_code: str
    created_at: datetime


@dataclass(frozen=True)
class TransferCommand:
    origin_account_id: str
    amount: str
    concept: str
    destination_account_number: str | None = None
    destination_cci: str | None = None
    destination_holder: str | None = None
    otp_code: str | None = None


@dataclass(frozen=True)
class ServiceDefinition:
    code: str
    name: str
    category: str
    reference_label: str
    reference_pattern: str
    min_amount: Decimal
    max_amount: Decimal


@dataclass(frozen=True)
class PaymentCommand:
    origin_account_id: str
    service_code: str
    reference: str
    amount: str
    otp_code: str | None = None


@dataclass
class Payment:
    id: str
    user_id: str
    account_id: str
    service_code: str
    service_name: str
    reference: str
    amount: Decimal
    operation_code: str
    created_at: datetime


@dataclass
class Card:
    id: str
    user_id: str
    account_id: str
    brand: CardBrand
    last4: str
    holder_name: str
    expiry_month: int
    expiry_year: int
    status: CardStatus
    is_virtual: bool


@dataclass
class Beneficiary:
    id: str
    user_id: str
    holder_name: str
    alias: str
    bank_name: str
    account_number: str | None
    cci: str | None
    created_at: datetime


@dataclass(frozen=True)
class BeneficiaryCommand:
    holder_name: str
    alias: str
    bank_name: str
    account_number: str | None = None
    cci: str | None = None


@dataclass(frozen=True)
class Branch:
    id: str
    name: str
    kind: BranchKind
    address: str
    district: str
    city: str
    latitude: float
    longitude: float
    hours: str
    phone: str


@dataclass
class RefreshToken:
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked: bool
    created_at: datetime


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True)
class LoginSuccess:
    requires_otp: bool
    tokens: TokenPair | None = None
    challenge_token: str | None = None
    challenge_expires_in: int | None = None


@dataclass(frozen=True)
class RegisterCommand:
    dni: str
    email: str
    phone: str
    given_names: str
    paternal_surname: str
    maternal_surname: str
    password: str


@dataclass(frozen=True)
class ProfilePatch:
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True)
class Page:
    items: list = field(default_factory=list)
    page: int = 1
    page_size: int = 20
    total: int = 0
