from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import DomainError

STATUS = {
    "VALIDATION": 422,
    "AMOUNT_TOO_SMALL": 422,
    "CCI_INVALID": 422,
    "CURRENCY": 422,
    "UNAUTHORIZED": 401,
    "OTP_INVALID": 401,
    "OTP_REQUIRED": 401,
    "FORBIDDEN": 403,
    "USER_BLOCKED": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "CTS_RESTRICTED": 409,
    "INSUFFICIENT_FUNDS": 409,
    "ACCOUNT_BLOCKED": 409,
    "DEST_UNAVAILABLE": 409,
    "SAME_ACCOUNT": 409,
    "LIMIT_EXCEEDED": 409,
    "DAILY_LIMIT": 409,
    "LOCKED": 423,
}


def error_body(code: str, message: str, details: list[str] | None = None) -> dict[str, object]:
    return {"code": code, "message": message, "details": details or []}


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain(_request, exc: DomainError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=STATUS.get(exc.code, 400))

    @app.exception_handler(RequestValidationError)
    async def shape(_request, exc: RequestValidationError) -> JSONResponse:
        details: list[str] = []
        for item in exc.errors():
            location = ".".join(str(part) for part in item.get("loc", []) if part != "body")
            message = str(item.get("msg", "dato inválido"))
            details.append(f"{location}: {message}" if location else message)
        return JSONResponse(
            error_body("VALIDATION", "El cuerpo de la petición no tiene la forma esperada.", details),
            status_code=422,
        )
