from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.cci import build_cci
from app.domain.ledger import post_story
from app.domain.money import money
from app.infrastructure.models import UserModel
from app.infrastructure.security import hash_password
from app.types.entities import (
    Account,
    Beneficiary,
    Card,
    Movement,
    StoryLine,
    User,
)
from app.infrastructure.repositories import (
    SqlAccountRepository,
    SqlBeneficiaryRepository,
    SqlCardRepository,
    SqlMovementRepository,
    SqlUserRepository,
)

DEMO_PASSWORD = "Andes.2026"
CARLOS_TOTP_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
NAMESPACE = uuid.UUID("6f1d8c2e-9a4b-4d1e-8c3a-0b7e5a1d2c90")


def stable_id(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE, name))


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _line(
    when: str,
    direction: str,
    amount: str,
    concept: str,
    counterparty: str,
    account: str = "",
    channel: str = "app",
) -> StoryLine:
    return StoryLine(
        occurred_at=_at(when),
        direction=direction,  # type: ignore[arg-type]
        amount=money(amount),
        concept=concept,
        counterparty_name=counterparty,
        counterparty_account=account,
        channel=channel,
    )


def seed_if_empty(session: Session, rounds: int = 12) -> None:
    existing = session.scalar(select(func.count()).select_from(UserModel)) or 0
    if existing:
        return
    users = SqlUserRepository(session)
    accounts = SqlAccountRepository(session)
    movements = SqlMovementRepository(session)
    cards = SqlCardRepository(session)
    beneficiaries = SqlBeneficiaryRepository(session)
    password_hash = hash_password(DEMO_PASSWORD, rounds)
    maria = _user(
        "user-maria",
        "45821367",
        "maria.quispe@correo.pe",
        "952418763",
        "María Elena",
        "Quispe",
        "Huanca",
        password_hash,
        None,
        False,
        "active",
        "2024-03-12T14:10:00-05:00",
    )
    carlos = _user(
        "user-carlos",
        "70129458",
        "carlos.mendoza@correo.pe",
        "953001284",
        "Carlos Alberto",
        "Mendoza",
        "Ríos",
        password_hash,
        CARLOS_TOTP_SECRET,
        True,
        "active",
        "2023-11-02T09:40:00-05:00",
    )
    lucia = _user(
        "user-lucia",
        "41290873",
        "lucia.choque@correo.pe",
        "961774520",
        "Lucía Fernanda",
        "Choque",
        "Mamani",
        password_hash,
        None,
        False,
        "active",
        "2025-01-20T11:05:00-05:00",
    )
    jorge = _user(
        "user-jorge",
        "33445566",
        "jorge.paredes@correo.pe",
        "952000111",
        "Jorge Luis",
        "Paredes",
        "Salas",
        password_hash,
        None,
        False,
        "blocked",
        "2022-08-01T08:00:00-05:00",
    )
    for person in (maria, carlos, lucia, jorge):
        users.add(person)
    session.flush()

    stories: list[tuple[Account, list[StoryLine]]] = [
        (
            _account("acct-maria-ahorro", maria.id, "ahorro", "00110000004821", "Ahorro soles", "2024-03-12T14:12:00-05:00"),
            [
                _line("2026-10-02T08:12:00-05:00", "credit", "3200.00", "Abono de haberes", "Logística del Sur SAC", channel="nomina"),
                _line("2026-10-03T19:41:00-05:00", "credit", "150.00", "Transferencia recibida", "Rosa Quispe Huanca", "00110000009901"),
                _line("2026-10-04T10:06:00-05:00", "debit", "86.40", "Pago de servicio Luz Andina", "Luz Andina", "10445821", "pago_servicio"),
                _line("2026-10-06T13:22:00-05:00", "debit", "142.80", "Compra Supermercados Collpa", "Supermercados Collpa", channel="pos"),
                _line("2026-10-07T18:03:00-05:00", "debit", "38.50", "Compra Botica San Pedro", "Botica San Pedro", channel="pos"),
                _line("2026-10-09T09:18:00-05:00", "debit", "500.00", "Transferencia enviada", "Carlos Alberto Mendoza Ríos", "00110000007751"),
                _line("2026-10-11T12:44:00-05:00", "debit", "200.00", "Retiro en cajero", "Agencia Centro", channel="cajero"),
                _line("2026-10-15T16:02:00-05:00", "debit", "850.00", "Pago Universidad Privada de Tacna", "Universidad Privada de Tacna", "20240018", "pago_servicio"),
                _line("2026-10-31T23:10:00-05:00", "credit", "4.15", "Intereses de ahorros", "AndesBank", channel="cargo_automatico"),
                _line("2026-11-02T07:55:00-05:00", "debit", "120.00", "Compra Grifo Los Ángeles", "Grifo Los Ángeles", channel="pos"),
                _line("2026-11-08T20:16:00-05:00", "credit", "75.00", "Transferencia recibida", "Lucía Fernanda Choque Mamani", "00110000003308"),
                _line("2026-11-18T06:30:00-05:00", "debit", "29.90", "Seguro Protección Andes", "Seguro Protección Andes", channel="cargo_automatico"),
                _line("2026-11-20T08:48:00-05:00", "debit", "64.30", "Compra Panadería La Esquina", "Panadería La Esquina", channel="pos"),
                _line("2026-11-24T08:05:00-05:00", "credit", "1800.00", "Abono de haberes", "Logística del Sur SAC", channel="nomina"),
            ],
        ),
        (
            _account("acct-maria-corriente", maria.id, "corriente", "00110000009034", "Corriente", "2024-06-01T10:00:00-05:00"),
            [
                _line("2026-10-01T09:00:00-05:00", "credit", "1500.00", "Transferencia entre cuentas propias", "María Elena Quispe Huanca", "00110000004821"),
                _line("2026-10-12T11:20:00-05:00", "debit", "89.90", "Compra Librería Universitaria", "Librería Universitaria", channel="pos"),
                _line("2026-11-03T21:14:00-05:00", "debit", "45.00", "Recarga Móvil Sur", "Móvil Sur", "952418763", "pago_servicio"),
                _line("2026-11-19T19:02:00-05:00", "debit", "210.00", "Cena Mercado Central", "Puesto 14 Mercado Central", channel="pos"),
            ],
        ),
        (
            _account("acct-maria-cts", maria.id, "cts", "00110000001102", "CTS", "2024-03-12T14:20:00-05:00"),
            [
                _line("2026-05-15T17:00:00-05:00", "credit", "8200.00", "Depósito CTS", "Logística del Sur SAC", channel="nomina"),
                _line("2026-11-14T17:05:00-05:00", "credit", "2100.00", "Depósito CTS", "Logística del Sur SAC", channel="nomina"),
            ],
        ),
        (
            _account("acct-carlos-ahorro", carlos.id, "ahorro", "00110000007751", "Ahorro soles", "2023-11-02T09:50:00-05:00"),
            [
                _line("2026-10-01T08:00:00-05:00", "credit", "4500.00", "Abono de haberes", "Consultores Arunta SAC", channel="nomina"),
                _line("2026-10-09T09:19:00-05:00", "credit", "500.00", "Transferencia recibida", "María Elena Quispe Huanca", "00110000004821"),
                _line("2026-10-18T15:40:00-05:00", "debit", "1260.00", "Pago de alquiler", "Inmobiliaria Tacna Norte", channel="transferencia"),
                _line("2026-11-05T13:11:00-05:00", "debit", "96.70", "Compra Minimarket El Alto", "Minimarket El Alto", channel="pos"),
                _line("2026-11-22T18:27:00-05:00", "debit", "350.00", "Transferencia enviada", "Colegio Santa María", "99800112345678901234", "transferencia"),
            ],
        ),
        (
            _account("acct-carlos-corriente", carlos.id, "corriente", "00110000006620", "Corriente", "2024-02-14T12:00:00-05:00"),
            [
                _line("2026-10-20T10:12:00-05:00", "credit", "800.00", "Transferencia entre cuentas propias", "Carlos Alberto Mendoza Ríos", "00110000007751"),
                _line("2026-11-09T09:33:00-05:00", "debit", "189.40", "Pago Luz Andina", "Luz Andina", "2288190", "pago_servicio"),
            ],
        ),
        (
            _account("acct-lucia-ahorro", lucia.id, "ahorro", "00110000003308", "Ahorro soles", "2025-01-20T11:10:00-05:00"),
            [
                _line("2026-10-28T08:20:00-05:00", "credit", "1200.00", "Abono de haberes", "Clínica del Altiplano", channel="nomina"),
                _line("2026-11-01T17:45:00-05:00", "debit", "320.00", "Compra Supermercado del Sur", "Supermercado del Sur", channel="pos"),
                _line("2026-11-08T20:15:00-05:00", "debit", "75.00", "Transferencia enviada", "María Elena Quispe Huanca", "00110000004821"),
                _line("2026-11-16T12:08:00-05:00", "debit", "48.90", "Compra Farmacia del Parque", "Farmacia del Parque", channel="pos"),
                _line("2026-11-23T19:50:00-05:00", "debit", "260.00", "Pago Agua Tacna", "Agua Tacna", "551902", "pago_servicio"),
            ],
        ),
    ]
    openings = {
        "acct-maria-ahorro": "8450.20",
        "acct-maria-corriente": "2295.80",
        "acct-maria-cts": "8340.00",
        "acct-carlos-ahorro": "2104.55",
        "acct-carlos-corriente": "640.15",
        "acct-lucia-ahorro": "0.00",
    }
    def _key(account: Account) -> str:
        mapping = {
            "00110000004821": "acct-maria-ahorro",
            "00110000009034": "acct-maria-corriente",
            "00110000001102": "acct-maria-cts",
            "00110000007751": "acct-carlos-ahorro",
            "00110000006620": "acct-carlos-corriente",
            "00110000003308": "acct-lucia-ahorro",
        }
        return mapping[account.number]

    staged: list[tuple[Account, list]] = []
    for account, lines in stories:
        balance, posted = post_story(money(openings[_key(account)]), lines)
        account.available_balance = balance
        accounts.add(account)
        staged.append((account, posted))
    session.flush()
    for account, posted in staged:
        for index, line in enumerate(posted, start=1):
            movements.add(
                Movement(
                    id=stable_id(f"mov-{account.number}-{index}"),
                    account_id=account.id,
                    direction=line.direction,
                    amount=line.amount,
                    balance_after=line.balance_after,
                    concept=line.concept,
                    counterparty_name=line.counterparty_name,
                    counterparty_account=line.counterparty_account,
                    channel=line.channel,
                    operation_code=f"AB-SEED-{account.number[-4:]}-{index:02d}",
                    occurred_at=line.occurred_at,
                )
            )
    session.flush()
    cards.add(_card("card-maria-visa", maria, "acct-maria-ahorro", "visa", "4412", 9, 2028, "active", False))
    cards.add(_card("card-maria-mc", maria, "acct-maria-corriente", "mastercard", "9088", 3, 2027, "active", True))
    cards.add(_card("card-carlos", carlos, "acct-carlos-ahorro", "visa", "6621", 12, 2028, "active", False))
    cards.add(_card("card-lucia", lucia, "acct-lucia-ahorro", "visa", "7730", 6, 2026, "blocked", False))
    beneficiaries.add(
        Beneficiary(
            id=stable_id("ben-maria-carlos"),
            user_id=maria.id,
            holder_name=carlos.full_name,
            alias="Carlos",
            bank_name="AndesBank",
            account_number="00110000007751",
            cci=None,
            created_at=_at("2026-09-01T10:00:00-05:00"),
        )
    )
    beneficiaries.add(
        Beneficiary(
            id=stable_id("ben-maria-externo"),
            user_id=maria.id,
            holder_name="Inversiones Colchane",
            alias="Proveedor",
            bank_name="Banco Demo Sur",
            account_number=None,
            cci="99800112345678901234",
            created_at=_at("2026-09-14T10:00:00-05:00"),
        )
    )
def _user(
    key: str,
    dni: str,
    email: str,
    phone: str,
    names: str,
    paternal: str,
    maternal: str,
    password_hash: str,
    totp_secret: str | None,
    totp_enabled: bool,
    status: str,
    created: str,
) -> User:
    return User(
        id=stable_id(key),
        dni=dni,
        email=email,
        phone=phone,
        given_names=names,
        paternal_surname=paternal,
        maternal_surname=maternal,
        password_hash=password_hash,
        totp_secret=totp_secret,
        totp_enabled=totp_enabled,
        status=status,  # type: ignore[arg-type]
        failed_attempts=0,
        locked_until=None,
        created_at=_at(created),
    )


def _account(key: str, user_id: str, product: str, number: str, alias: str, opened: str) -> Account:
    return Account(
        id=stable_id(key),
        user_id=user_id,
        product_type=product,  # type: ignore[arg-type]
        number=number,
        cci=build_cci(number),
        currency="PEN",
        available_balance=money("0.00"),
        status="active",
        alias=alias,
        opened_on=_at(opened),
    )


def _card(
    key: str,
    user: User,
    account_key: str,
    brand: str,
    last4: str,
    month: int,
    year: int,
    status: str,
    virtual: bool,
) -> Card:
    return Card(
        id=stable_id(key),
        user_id=user.id,
        account_id=stable_id(account_key),
        brand=brand,  # type: ignore[arg-type]
        last4=last4,
        holder_name=user.full_name.upper(),
        expiry_month=month,
        expiry_year=year,
        status=status,  # type: ignore[arg-type]
        is_virtual=virtual,
    )
