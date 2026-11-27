from __future__ import annotations

from app.domain.errors import DomainError
from app.domain.policies import product_label
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import Account, Movement


class AccountService:
    def list_for(self, uow: SqlUnitOfWork, user_id: str) -> list[Account]:
        return uow.accounts.list_by_user(user_id)

    def get(self, uow: SqlUnitOfWork, user_id: str, account_id: str) -> Account:
        account = uow.accounts.get(account_id)
        if account is None or account.user_id != user_id:
            raise DomainError("NOT_FOUND", "La cuenta no existe.")
        return account

    def movements(
        self, uow: SqlUnitOfWork, user_id: str, account_id: str, page: int, page_size: int
    ) -> tuple[list[Movement], int]:
        self.get(uow, user_id, account_id)
        return uow.movements.list_by_account(account_id, page, page_size)

    def label(self, account: Account) -> str:
        return product_label(account.product_type)
