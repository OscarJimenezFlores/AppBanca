from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.repositories import (
    SqlAccountRepository,
    SqlBeneficiaryRepository,
    SqlCardRepository,
    SqlMovementRepository,
    SqlPaymentRepository,
    SqlTokenRepository,
    SqlTransferRepository,
    SqlUserRepository,
)


class SqlUnitOfWork:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = SqlUserRepository(session)
        self.accounts = SqlAccountRepository(session)
        self.movements = SqlMovementRepository(session)
        self.transfers = SqlTransferRepository(session)
        self.payments = SqlPaymentRepository(session)
        self.cards = SqlCardRepository(session)
        self.beneficiaries = SqlBeneficiaryRepository(session)
        self.tokens = SqlTokenRepository(session)
