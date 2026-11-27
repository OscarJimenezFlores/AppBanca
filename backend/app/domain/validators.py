from __future__ import annotations

import re
import unicodedata

from app.domain.errors import DomainError

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")
COMMON_PASSWORDS = {
    "password",
    "12345678",
    "123456789",
    "qwerty123",
    "andesbank",
    "andes.2026",
}


def clean_spaces(value: str) -> str:
    return " ".join((value or "").split())


def reject_controls(value: str) -> None:
    for char in value:
        if unicodedata.category(char).startswith("C"):
            raise DomainError("VALIDATION", "El texto contiene caracteres de control.", [])


def dni_error(value: str) -> str | None:
    text = (value or "").strip()
    if not re.fullmatch(r"\d{8}", text):
        return "El DNI debe tener 8 dígitos."
    if text == "00000000":
        return "El DNI no es válido."
    return None


def phone_error(value: str) -> str | None:
    text = (value or "").strip()
    if not re.fullmatch(r"9\d{8}", text):
        return "El celular debe tener 9 dígitos y empezar con 9."
    return None


def email_error(value: str) -> str | None:
    text = (value or "").strip().lower()
    if len(text) >= 160 or not EMAIL_RE.fullmatch(text):
        return "El correo no tiene un formato utilizable."
    return None


def name_error(value: str, label: str) -> str | None:
    raw = value or ""
    try:
        reject_controls(raw)
    except DomainError:
        return f"{label} contiene caracteres no permitidos."
    text = clean_spaces(raw)
    if not 2 <= len(text) <= 80 or not NAME_RE.fullmatch(text):
        return f"{label} debe tener entre 2 y 80 letras."
    return None


def password_errors(password: str) -> list[str]:
    errors: list[str] = []
    if password is None:
        return ["La clave es obligatoria."]
    if len(password) < 8:
        errors.append("La clave debe tener al menos 8 caracteres.")
    if len(password) > 64:
        errors.append("La clave no debe superar 64 caracteres.")
    if not re.search(r"[A-Z]", password):
        errors.append("La clave debe incluir una mayúscula.")
    if not re.search(r"[a-z]", password):
        errors.append("La clave debe incluir una minúscula.")
    if not re.search(r"\d", password):
        errors.append("La clave debe incluir un dígito.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("La clave debe incluir un símbolo.")
    if password.lower() in COMMON_PASSWORDS or "andesbank" in password.lower():
        errors.append("La clave es demasiado predecible.")
    return errors


def otp_error(code: str | None) -> str | None:
    if not code or not re.fullmatch(r"\d{6}", code):
        return "El código debe tener 6 dígitos."
    return None


def account_number_error(value: str) -> str | None:
    if not re.fullmatch(r"\d{14}", value or ""):
        return "El número de cuenta debe tener 14 dígitos."
    return None


def cci_shape_error(value: str) -> str | None:
    if not re.fullmatch(r"\d{20}", value or ""):
        return "El CCI debe tener 20 dígitos."
    return None


def concept_error(value: str, label: str = "El concepto", max_len: int = 80) -> str | None:
    text = clean_spaces(value or "")
    try:
        reject_controls(value or "")
    except DomainError:
        return f"{label} contiene caracteres no permitidos."
    if not text:
        return f"{label} es obligatorio."
    if len(text) > max_len:
        return f"{label} admite como máximo {max_len} caracteres."
    return None


def require(errors: list[str]) -> None:
    if errors:
        raise DomainError("VALIDATION", "Hay datos que no pasan la validación.", errors)
