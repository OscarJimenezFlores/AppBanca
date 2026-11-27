from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import pyotp

from app.types.ports import Clock


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def hash_password(password: str, rounds: int = 12) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _stamp(moment: datetime) -> int:
    return int(moment.timestamp())


def encode_token(secret: str, subject: str, typ: str, issued: datetime, expires: datetime) -> str:
    payload = {"sub": subject, "typ": typ, "iat": _stamp(issued), "exp": _stamp(expires)}
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(secret: str, token: str, expected_type: str) -> str:
    from app.domain.errors import DomainError

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.") from exc
    if payload.get("typ") != expected_type or not payload.get("sub"):
        raise DomainError("UNAUTHORIZED", "La sesión no es válida o ya venció.")
    return str(payload["sub"])


def access_token(secret: str, user_id: str, clock: Clock, minutes: int) -> tuple[str, int]:
    issued = clock.now()
    expires = issued + timedelta(minutes=minutes)
    return encode_token(secret, user_id, "access", issued, expires), minutes * 60


def challenge_token(secret: str, user_id: str, clock: Clock) -> tuple[str, int]:
    issued = clock.now()
    expires = issued + timedelta(minutes=5)
    return encode_token(secret, user_id, "otp", issued, expires), 300


def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="AndesBank")


def totp_matches(secret: str, code: str, moment: datetime) -> bool:
    if secret is None:
        return False
    from app.domain.validators import otp_error

    if otp_error(code):
        return False
    return bool(pyotp.TOTP(secret).verify(code, for_time=moment, valid_window=1))
