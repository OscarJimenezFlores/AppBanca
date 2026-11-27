from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.branch_service import list_branches
from app.application.security_service import SecurityService
from app.infrastructure.uow import SqlUnitOfWork
from app.presentation.deps import current_user, get_security_service, get_uow
from app.presentation.schemas import DisableTotpIn, TotpCodeIn
from app.types.entities import User

router = APIRouter(prefix="/api/v1", tags=["Seguridad y agencias"])


@router.post("/security/totp/setup")
def setup_totp(
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: SecurityService = Depends(get_security_service),
):
    return service.begin_totp(uow, user)


@router.post("/security/totp/confirm", status_code=204)
def confirm_totp(
    body: TotpCodeIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: SecurityService = Depends(get_security_service),
):
    service.confirm_totp(uow, user, body.code)
    return None


@router.post("/security/totp/disable", status_code=204)
def disable_totp(
    body: DisableTotpIn,
    user: User = Depends(current_user),
    uow: SqlUnitOfWork = Depends(get_uow),
    service: SecurityService = Depends(get_security_service),
):
    service.disable_totp(uow, user, body.password, body.code)
    return None


@router.get("/branches")
def branches(
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
    user: User = Depends(current_user),
):
    return list_branches(latitude, longitude)
