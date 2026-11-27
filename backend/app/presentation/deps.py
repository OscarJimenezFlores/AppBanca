from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.account_service import AccountService
from app.application.auth_service import AuthService
from app.application.directory_service import BeneficiaryService, CardService
from app.application.payment_service import PaymentService
from app.application.profile_service import ProfileService
from app.application.security_service import SecurityService
from app.application.transfer_service import TransferService
from app.domain.errors import DomainError
from app.infrastructure.config import Settings, load_settings
from app.infrastructure.security import SystemClock, decode_token
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import User

bearer = HTTPBearer(auto_error=False)


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def get_clock() -> SystemClock:
    return SystemClock()


def password_rounds(settings: Settings = Depends(get_settings)) -> int:
    return 4 if settings.app_env == "test" else 12


def get_session(request: Request):
    session = Session(request.app.state.engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_uow(session: Session = Depends(get_session)) -> SqlUnitOfWork:
    return SqlUnitOfWork(session)


def get_auth_service(
    settings: Settings = Depends(get_settings),
    clock: SystemClock = Depends(get_clock),
    rounds: int = Depends(password_rounds),
) -> AuthService:
    return AuthService(settings, clock, rounds)


def get_transfer_service(clock: SystemClock = Depends(get_clock)) -> TransferService:
    return TransferService(clock)


def get_payment_service(clock: SystemClock = Depends(get_clock)) -> PaymentService:
    return PaymentService(clock)


def get_security_service(clock: SystemClock = Depends(get_clock)) -> SecurityService:
    return SecurityService(clock)


def get_profile_service(
    clock: SystemClock = Depends(get_clock),
    rounds: int = Depends(password_rounds),
) -> ProfileService:
    return ProfileService(clock, rounds)


def get_beneficiary_service(clock: SystemClock = Depends(get_clock)) -> BeneficiaryService:
    return BeneficiaryService(clock)


def get_account_service() -> AccountService:
    return AccountService()


def get_card_service() -> CardService:
    return CardService()


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    uow: SqlUnitOfWork = Depends(get_uow),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise DomainError("UNAUTHORIZED", "Falta el token de acceso.")
    user_id = decode_token(settings.jwt_secret, credentials.credentials, "access")
    user = uow.users.get_by_id(user_id)
    if user is None or user.status == "blocked":
        raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
    return user


def build_engine(settings: Settings):
    return create_engine(settings.database_url, pool_pre_ping=True)
