from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.account_service import AccountService
from app.application.directory_service import BeneficiaryService, CardService
from app.application.payment_service import PaymentService
from app.application.profile_service import ProfileService
from app.application.transfer_service import TransferService
from app.domain.catalog import SERVICES
from app.infrastructure.uow import SqlUnitOfWork
from app.presentation.deps import (
    current_user,
    get_account_service,
    get_beneficiary_service,
    get_card_service,
    get_payment_service,
    get_profile_service,
    get_transfer_service,
    get_uow,
)
from app.presentation.presenters import (
    account_out,
    beneficiary_out,
    card_out,
    movement_out,
    page_out,
    payment_out,
    transfer_out,
    user_out,
)
from app.presentation.schemas import BeneficiaryIn, PasswordIn, PaymentIn, ProfileIn, TransferIn
from app.types.entities import BeneficiaryCommand, PaymentCommand, ProfilePatch, TransferCommand, User

router = APIRouter(prefix="/api/v1", tags=["Banca"])


@router.patch("/me")
def patch_me(
    body: ProfileIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: ProfileService = Depends(get_profile_service),
):
    updated = service.update(uow, user, ProfilePatch(email=body.email, phone=body.phone))
    return user_out(updated)


@router.post("/me/password", status_code=204)
def change_password(
    body: PasswordIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: ProfileService = Depends(get_profile_service),
):
    service.change_password(uow, user, body.current_password, body.new_password, body.otp_code)
    return None


@router.get("/accounts")
def list_accounts(
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: AccountService = Depends(get_account_service),
):
    return [account_out(item) for item in service.list_for(uow, user.id)]


@router.get("/accounts/{account_id}")
def get_account(
    account_id: str,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: AccountService = Depends(get_account_service),
):
    return account_out(service.get(uow, user.id, account_id))


@router.get("/accounts/{account_id}/movements")
def movements(
    account_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: AccountService = Depends(get_account_service),
):
    items, total = service.movements(uow, user.id, account_id, page, page_size)
    return page_out([movement_out(item) for item in items], page, page_size, total)


@router.post("/transfers", status_code=201)
def create_transfer(
    body: TransferIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: TransferService = Depends(get_transfer_service),
):
    created = service.create(
        uow,
        user.id,
        TransferCommand(
            origin_account_id=body.origin_account_id,
            amount=body.amount,
            concept=body.concept,
            destination_account_number=body.destination_account_number,
            destination_cci=body.destination_cci,
            destination_holder=body.destination_holder,
            otp_code=body.otp_code,
        ),
    )
    return transfer_out(created)


@router.get("/transfers/{transfer_id}")
def get_transfer(
    transfer_id: str,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: TransferService = Depends(get_transfer_service),
):
    return transfer_out(service.get(uow, user.id, transfer_id))


@router.get("/payments/services")
def services(user: User = Depends(current_user)):
    return [
        {
            "code": item.code,
            "name": item.name,
            "category": item.category,
            "reference_label": item.reference_label,
            "reference_pattern": item.reference_pattern,
            "min_amount": f"{item.min_amount:.2f}",
            "max_amount": f"{item.max_amount:.2f}",
        }
        for item in SERVICES
    ]


@router.post("/payments", status_code=201)
def pay(
    body: PaymentIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: PaymentService = Depends(get_payment_service),
):
    created = service.pay(
        uow,
        user.id,
        PaymentCommand(
            origin_account_id=body.origin_account_id,
            service_code=body.service_code,
            reference=body.reference,
            amount=body.amount,
            otp_code=body.otp_code,
        ),
    )
    return payment_out(created)


@router.get("/payments")
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: PaymentService = Depends(get_payment_service),
):
    items, total = service.list_for(uow, user.id, page, page_size)
    return page_out([payment_out(item) for item in items], page, page_size, total)


@router.get("/cards")
def list_cards(
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    cards: CardService = Depends(get_card_service),
    accounts: AccountService = Depends(get_account_service),
):
    return [card_out(item, accounts, uow) for item in cards.list_for(uow, user.id)]


@router.post("/cards/{card_id}/block")
def block_card(
    card_id: str,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    cards: CardService = Depends(get_card_service),
    accounts: AccountService = Depends(get_account_service),
):
    return card_out(cards.set_blocked(uow, user.id, card_id, True), accounts, uow)


@router.post("/cards/{card_id}/unblock")
def unblock_card(
    card_id: str,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    cards: CardService = Depends(get_card_service),
    accounts: AccountService = Depends(get_account_service),
):
    return card_out(cards.set_blocked(uow, user.id, card_id, False), accounts, uow)


@router.get("/beneficiaries")
def list_beneficiaries(
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: BeneficiaryService = Depends(get_beneficiary_service),
):
    return [beneficiary_out(item) for item in service.list_for(uow, user.id)]


@router.post("/beneficiaries", status_code=201)
def add_beneficiary(
    body: BeneficiaryIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: BeneficiaryService = Depends(get_beneficiary_service),
):
    created = service.add(
        uow,
        user.id,
        BeneficiaryCommand(
            holder_name=body.holder_name,
            alias=body.alias,
            bank_name=body.bank_name,
            account_number=body.account_number,
            cci=body.cci,
        ),
    )
    return beneficiary_out(created)


@router.delete("/beneficiaries/{beneficiary_id}", status_code=204)
def delete_beneficiary(
    beneficiary_id: str,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: BeneficiaryService = Depends(get_beneficiary_service),
):
    service.delete(uow, user.id, beneficiary_id)
    return None
