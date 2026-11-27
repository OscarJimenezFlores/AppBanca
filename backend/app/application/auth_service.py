from __future__ import annotations

from datetime import timedelta

from app.domain.access import assert_user_can_authenticate, note_failed_secret, note_successful_secret
from app.domain.cci import build_cci
from app.domain.errors import DomainError
from app.domain.ids import new_id
from app.domain.money import money
from app.domain.validators import (
    dni_error,
    email_error,
    name_error,
    password_errors,
    phone_error,
    require,
)
from app.infrastructure.config import Settings
from app.infrastructure.security import (
    access_token,
    challenge_token,
    decode_token,
    hash_password,
    hash_token,
    new_refresh_token,
    totp_matches,
    verify_password,
)
from app.infrastructure.uow import SqlUnitOfWork
from app.types.entities import Account, LoginSuccess, RefreshToken, RegisterCommand, TokenPair, User
from app.types.ports import Clock


class AuthService:
    def __init__(self, settings: Settings, clock: Clock, password_rounds: int = 12) -> None:
        self.settings = settings
        self.clock = clock
        self.password_rounds = password_rounds

    def register(self, uow: SqlUnitOfWork, command: RegisterCommand) -> LoginSuccess:
        email = (command.email or "").strip().lower()
        errors = [
            item
            for item in (
                dni_error(command.dni),
                email_error(email),
                phone_error(command.phone),
                name_error(command.given_names, "Los nombres"),
                name_error(command.paternal_surname, "El apellido paterno"),
                name_error(command.maternal_surname, "El apellido materno"),
            )
            if item
        ]
        errors.extend(password_errors(command.password))
        require(errors)
        if uow.users.get_by_dni(command.dni.strip()):
            raise DomainError("CONFLICT", "Ya existe un cliente con ese DNI.")
        if uow.users.get_by_email(email):
            raise DomainError("CONFLICT", "Ya existe un cliente con ese correo.")
        now = self.clock.now()
        user = User(
            id=new_id(),
            dni=command.dni.strip(),
            email=email,
            phone=command.phone.strip(),
            given_names=" ".join(command.given_names.split()),
            paternal_surname=" ".join(command.paternal_surname.split()),
            maternal_surname=" ".join(command.maternal_surname.split()),
            password_hash=hash_password(command.password, self.password_rounds),
            totp_secret=None,
            totp_enabled=False,
            status="active",
            failed_attempts=0,
            locked_until=None,
            created_at=now,
        )
        uow.users.add(user)
        number = uow.accounts.next_number()
        uow.accounts.add(
            Account(
                id=new_id(),
                user_id=user.id,
                product_type="ahorro",
                number=number,
                cci=build_cci(number),
                currency="PEN",
                available_balance=money("0.00"),
                status="active",
                alias="Ahorro soles",
                opened_on=now,
            )
        )
        return LoginSuccess(requires_otp=False, tokens=self._issue(uow, user))

    def login(self, uow: SqlUnitOfWork, identifier: str, password: str) -> LoginSuccess:
        user = self._find(uow, identifier)
        now = self.clock.now()
        if user is None:
            raise DomainError("UNAUTHORIZED", "Credenciales inválidas.")
        assert_user_can_authenticate(user, now)
        if not verify_password(password or "", user.password_hash):
            note_failed_secret(user, now)
            uow.users.update(user)
            if user.locked_until is not None and user.locked_until > now:
                raise DomainError(
                    "LOCKED",
                    "Demasiados intentos fallidos. La clave queda suspendida 15 minutos.",
                )
            raise DomainError("UNAUTHORIZED", "Credenciales inválidas.")
        note_successful_secret(user)
        uow.users.update(user)
        if user.totp_enabled:
            token, expires_in = challenge_token(self.settings.jwt_secret, user.id, self.clock)
            return LoginSuccess(
                requires_otp=True,
                challenge_token=token,
                challenge_expires_in=expires_in,
            )
        return LoginSuccess(requires_otp=False, tokens=self._issue(uow, user))

    def verify_otp(self, uow: SqlUnitOfWork, challenge: str, code: str) -> TokenPair:
        user_id = decode_token(self.settings.jwt_secret, challenge, "otp")
        user = uow.users.get_by_id(user_id)
        now = self.clock.now()
        if user is None or not user.totp_enabled or not user.totp_secret:
            raise DomainError("UNAUTHORIZED", "La verificación adicional no está disponible.")
        assert_user_can_authenticate(user, now)
        if not totp_matches(user.totp_secret, code, now):
            note_failed_secret(user, now)
            uow.users.update(user)
            raise DomainError("OTP_INVALID", "El código del autenticador no coincide.")
        note_successful_secret(user)
        uow.users.update(user)
        return self._issue(uow, user)

    def refresh(self, uow: SqlUnitOfWork, raw_token: str) -> TokenPair:
        stored = uow.tokens.get_by_hash(hash_token(raw_token or ""))
        now = self.clock.now()
        if stored is None or stored.revoked or stored.expires_at <= now:
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        user = uow.users.get_by_id(stored.user_id)
        if user is None or user.status != "active":
            raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
        stored.revoked = True
        uow.tokens.save(stored)
        return self._issue(uow, user)

    def logout(self, uow: SqlUnitOfWork, raw_token: str) -> None:
        stored = uow.tokens.get_by_hash(hash_token(raw_token or ""))
        if stored is not None and not stored.revoked:
            stored.revoked = True
            uow.tokens.save(stored)

    def _issue(self, uow: SqlUnitOfWork, user: User) -> TokenPair:
        token, expires_in = access_token(
            self.settings.jwt_secret,
            user.id,
            self.clock,
            self.settings.access_token_minutes,
        )
        raw = new_refresh_token()
        now = self.clock.now()
        uow.tokens.add(
            RefreshToken(
                id=new_id(),
                user_id=user.id,
                token_hash=hash_token(raw),
                expires_at=now + timedelta(days=self.settings.refresh_token_days),
                revoked=False,
                created_at=now,
            )
        )
        return TokenPair(access_token=token, refresh_token=raw, expires_in=expires_in)

    def _find(self, uow: SqlUnitOfWork, identifier: str) -> User | None:
        text = (identifier or "").strip()
        if text.isdigit():
            if dni_error(text):
                return None
            return uow.users.get_by_dni(text)
        if email_error(text):
            return None
        return uow.users.get_by_email(text.lower())
