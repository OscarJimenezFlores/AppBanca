from __future__ import annotations

from app.domain.errors import DomainError
from app.infrastructure.security import new_totp_secret, totp_matches, totp_uri, verify_password
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import User
from app.types.ports import Clock


class SecurityService:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def begin_totp(self, uow: SqlUnitOfWork, user: User) -> dict[str, str | int]:
        current = uow.users.get_for_update(user.id)
        if current is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        if current.totp_enabled:
            raise DomainError("CONFLICT", "El factor de doble autenticación ya está activo.")
        secret = new_totp_secret()
        current.totp_secret = secret
        current.totp_enabled = False
        uow.users.update(current)
        return {
            "secret": secret,
            "otpauth_uri": totp_uri(secret, current.email),
            "issuer": "AndesBank",
            "account": current.email,
            "digits": 6,
            "period": 30,
            "algorithm": "SHA1",
        }

    def confirm_totp(self, uow: SqlUnitOfWork, user: User, code: str) -> None:
        current = uow.users.get_for_update(user.id)
        if current is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        if current.totp_enabled:
            raise DomainError("CONFLICT", "El factor de doble autenticación ya está activo.")
        if not current.totp_secret or not totp_matches(current.totp_secret, code, self.clock.now()):
            raise DomainError("OTP_INVALID", "El código del autenticador no coincide. Genere uno nuevo y confirme.")
        current.totp_enabled = True
        uow.users.update(current)

    def disable_totp(self, uow: SqlUnitOfWork, user: User, password: str, code: str) -> None:
        current = uow.users.get_for_update(user.id)
        if current is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        if not current.totp_enabled or not current.totp_secret:
            raise DomainError("CONFLICT", "El factor de doble autenticación no está activo.")
        if not verify_password(password or "", current.password_hash):
            raise DomainError("UNAUTHORIZED", "La clave no coincide.")
        if not totp_matches(current.totp_secret, code, self.clock.now()):
            raise DomainError("OTP_INVALID", "El código del autenticador no coincide.")
        current.totp_enabled = False
        current.totp_secret = None
        uow.users.update(current)
