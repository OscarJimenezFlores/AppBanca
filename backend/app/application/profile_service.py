from __future__ import annotations

from app.domain.errors import DomainError
from app.domain.validators import email_error, otp_error, password_errors, phone_error, require
from app.infrastructure.security import hash_password, totp_matches, verify_password
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import ProfilePatch, User
from app.types.ports import Clock


class ProfileService:
    def __init__(self, clock: Clock, password_rounds: int = 12) -> None:
        self.clock = clock
        self.password_rounds = password_rounds

    def update(self, uow: SqlUnitOfWork, user: User, patch: ProfilePatch) -> User:
        current = uow.users.get_for_update(user.id)
        if current is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        errors: list[str] = []
        email = current.email
        phone = current.phone
        if patch.email is not None:
            email = patch.email.strip().lower()
            problem = email_error(email)
            if problem:
                errors.append(problem)
        if patch.phone is not None:
            phone = patch.phone.strip()
            problem = phone_error(phone)
            if problem:
                errors.append(problem)
        require(errors)
        if email != current.email and uow.users.get_by_email(email) is not None:
            raise DomainError("CONFLICT", "Ya existe un cliente con ese correo.")
        current.email = email
        current.phone = phone
        uow.users.update(current)
        return current

    def change_password(self, uow: SqlUnitOfWork, user: User, current_password: str, new_password: str, otp_code: str | None) -> None:
        current = uow.users.get_for_update(user.id)
        if current is None:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        if not verify_password(current_password or "", current.password_hash):
            raise DomainError("UNAUTHORIZED", "La clave actual no coincide.")
        errors = password_errors(new_password)
        if new_password == current_password:
            errors.append("La clave nueva tiene que ser distinta de la actual.")
        require(errors)
        if current.totp_enabled:
            problem = otp_error(otp_code)
            if problem or not current.totp_secret or not totp_matches(current.totp_secret, otp_code or "", self.clock.now()):
                raise DomainError("OTP_INVALID", "El código del autenticador no coincide.")
        current.password_hash = hash_password(new_password, self.password_rounds)
        uow.users.update(current)
        uow.tokens.revoke_all(current.id)
