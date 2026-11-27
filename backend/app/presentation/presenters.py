from __future__ import annotations

from app.application.account_service import AccountService
from app.domain.masking import group_account, group_cci, mask_account, mask_cci, mask_phone
from app.domain.money import money_str
from app.domain.policies import product_label
from app.types.entities import Account, Beneficiary, Card, LoginSuccess, Movement, Payment, TokenPair, Transfer, User


def tokens_from(result: LoginSuccess | TokenPair) -> dict[str, object]:
    pair = result if isinstance(result, TokenPair) else result.tokens
    challenge = None if isinstance(result, TokenPair) else result.challenge_token
    requires = False if isinstance(result, TokenPair) else result.requires_otp
    expires = pair.expires_in if pair else (None if isinstance(result, TokenPair) else result.challenge_expires_in)
    return {
        "requires_otp": requires,
        "token_type": "Bearer",
        "access_token": None if pair is None else pair.access_token,
        "refresh_token": None if pair is None else pair.refresh_token,
        "challenge_token": challenge,
        "expires_in": expires,
    }


def user_out(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "dni": user.dni,
        "email": user.email,
        "phone": user.phone,
        "phone_masked": mask_phone(user.phone),
        "given_names": user.given_names,
        "paternal_surname": user.paternal_surname,
        "maternal_surname": user.maternal_surname,
        "full_name": user.full_name,
        "status": user.status,
        "totp_enabled": user.totp_enabled,
        "created_at": user.created_at.isoformat(),
    }


def account_out(account: Account) -> dict[str, object]:
    return {
        "id": account.id,
        "product_type": account.product_type,
        "product_label": product_label(account.product_type),
        "alias": account.alias,
        "number": account.number,
        "number_masked": mask_account(account.number),
        "number_formatted": group_account(account.number),
        "cci": account.cci,
        "cci_masked": mask_cci(account.cci),
        "cci_formatted": group_cci(account.cci),
        "currency": account.currency,
        "available_balance": money_str(account.available_balance),
        "status": account.status,
        "opened_on": account.opened_on.isoformat(),
    }


def movement_out(item: Movement) -> dict[str, object]:
    return {
        "id": item.id,
        "direction": item.direction,
        "amount": money_str(item.amount),
        "balance_after": money_str(item.balance_after),
        "concept": item.concept,
        "counterparty_name": item.counterparty_name,
        "counterparty_account": item.counterparty_account,
        "channel": item.channel,
        "operation_code": item.operation_code,
        "occurred_at": item.occurred_at.isoformat(),
        "transfer_id": item.transfer_id,
        "payment_id": item.payment_id,
    }


def transfer_out(item: Transfer) -> dict[str, object]:
    return {
        "id": item.id,
        "origin_account_id": item.origin_account_id,
        "destination_account_id": item.destination_account_id,
        "destination_number": item.destination_number,
        "destination_holder": item.destination_holder,
        "amount": money_str(item.amount),
        "commission": money_str(item.commission),
        "concept": item.concept,
        "kind": item.kind,
        "status": item.status,
        "operation_code": item.operation_code,
        "created_at": item.created_at.isoformat(),
    }


def payment_out(item: Payment) -> dict[str, object]:
    return {
        "id": item.id,
        "account_id": item.account_id,
        "service_code": item.service_code,
        "service_name": item.service_name,
        "reference": item.reference,
        "amount": money_str(item.amount),
        "operation_code": item.operation_code,
        "created_at": item.created_at.isoformat(),
    }


def card_out(item: Card, accounts: AccountService, uow) -> dict[str, object]:
    account = uow.accounts.get(item.account_id)
    return {
        "id": item.id,
        "account_id": item.account_id,
        "account_alias": None if account is None else account.alias,
        "brand": item.brand,
        "pan_masked": f"•••• •••• •••• {item.last4}",
        "last4": item.last4,
        "holder_name": item.holder_name,
        "expiry_month": item.expiry_month,
        "expiry_year": item.expiry_year,
        "expiry": f"{item.expiry_month:02d}/{item.expiry_year}",
        "status": item.status,
        "is_virtual": item.is_virtual,
    }


def beneficiary_out(item: Beneficiary) -> dict[str, object]:
    return {
        "id": item.id,
        "holder_name": item.holder_name,
        "alias": item.alias,
        "bank_name": item.bank_name,
        "account_number": item.account_number,
        "account_masked": None if not item.account_number else mask_account(item.account_number),
        "cci": item.cci,
        "cci_masked": None if not item.cci else mask_cci(item.cci),
        "created_at": item.created_at.isoformat(),
    }


def page_out(items: list[dict[str, object]], page: int, page_size: int, total: int) -> dict[str, object]:
    return {"items": items, "page": page, "page_size": page_size, "total": total}
