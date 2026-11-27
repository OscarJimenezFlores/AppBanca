from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterIn(ApiModel):
    dni: str
    email: str
    phone: str
    given_names: str
    paternal_surname: str
    maternal_surname: str
    password: str = Field(min_length=1, max_length=64)


class LoginIn(ApiModel):
    identifier: str
    password: str = Field(min_length=1, max_length=64)


class OtpIn(ApiModel):
    challenge_token: str
    code: str


class RefreshIn(ApiModel):
    refresh_token: str


class LogoutIn(ApiModel):
    refresh_token: str


class ProfileIn(ApiModel):
    email: str | None = None
    phone: str | None = None


class PasswordIn(ApiModel):
    current_password: str
    new_password: str = Field(min_length=1, max_length=64)
    otp_code: str | None = None


class TotpCodeIn(ApiModel):
    code: str


class DisableTotpIn(ApiModel):
    password: str
    code: str


class TransferIn(ApiModel):
    origin_account_id: str
    amount: str
    concept: str
    destination_account_number: str | None = None
    destination_cci: str | None = None
    destination_holder: str | None = None
    otp_code: str | None = None


class PaymentIn(ApiModel):
    origin_account_id: str
    service_code: str
    reference: str
    amount: str
    otp_code: str | None = None


class BeneficiaryIn(ApiModel):
    holder_name: str
    alias: str
    bank_name: str
    account_number: str | None = None
    cci: str | None = None
