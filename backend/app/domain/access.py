from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.errors import DomainError
from app.domain.policies import LOCK_MINUTES, LOGIN_LOCK_ATTEMPTS
from app.types.entities import User


def assert_user_can_authenticate(user: User, now: datetime) -> None:
    if user.status == "blocked":
        raise DomainError(
            "USER_BLOCKED",
            "El usuario no puede operar. La revisión se hace en una agencia.",
        )
    if user.locked_until is not None and user.locked_until > now:
        raise DomainError(
            "LOCKED",
            "Demasiados intentos fallidos. La clave queda suspendida 15 minutos.",
        )


def note_failed_secret(user: User, now: datetime) -> None:
    user.failed_attempts += 1
    if user.failed_attempts >= LOGIN_LOCK_ATTEMPTS:
        user.locked_until = now + timedelta(minutes=LOCK_MINUTES)


def note_successful_secret(user: User) -> None:
    user.failed_attempts = 0
    user.locked_until = None
