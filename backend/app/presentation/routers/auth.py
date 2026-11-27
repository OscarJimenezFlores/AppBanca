from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.auth_service import AuthService
from app.infrastructure.uow import SqlUnitOfWork
from app.presentation.deps import current_user, get_auth_service, get_uow
from app.presentation.presenters import tokens_from, user_out
from app.presentation.schemas import LoginIn, LogoutIn, OtpIn, RefreshIn, RegisterIn
from app.types.entities import RegisterCommand, User

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/register", status_code=201)
def register(body: RegisterIn, uow: SqlUnitOfWork = Depends(get_uow), service: AuthService = Depends(get_auth_service)):
    result = service.register(
        uow,
        RegisterCommand(
            dni=body.dni,
            email=body.email,
            phone=body.phone,
            given_names=body.given_names,
            paternal_surname=body.paternal_surname,
            maternal_surname=body.maternal_surname,
            password=body.password,
        ),
    )
    return tokens_from(result)


@router.post("/login")
def login(body: LoginIn, uow: SqlUnitOfWork = Depends(get_uow), service: AuthService = Depends(get_auth_service)):
    return tokens_from(service.login(uow, body.identifier, body.password))


@router.post("/otp")
def otp(body: OtpIn, uow: SqlUnitOfWork = Depends(get_uow), service: AuthService = Depends(get_auth_service)):
    return tokens_from(service.verify_otp(uow, body.challenge_token, body.code))


@router.post("/refresh")
def refresh(body: RefreshIn, uow: SqlUnitOfWork = Depends(get_uow), service: AuthService = Depends(get_auth_service)):
    return tokens_from(service.refresh(uow, body.refresh_token))


@router.post("/logout", status_code=204)
def logout(body: LogoutIn, uow: SqlUnitOfWork = Depends(get_uow), service: AuthService = Depends(get_auth_service)):
    service.logout(uow, body.refresh_token)
    return None


me = APIRouter(prefix="/api/v1", tags=["Perfil"])


@me.get("/me")
def read_me(user: User = Depends(current_user)):
    return user_out(user)
