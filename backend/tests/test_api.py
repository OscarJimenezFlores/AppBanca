import os

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.dev.create_database import assert_safe_test_database
from app.infrastructure.models import Base
from app.infrastructure.seed import CARLOS_TOTP_SECRET, DEMO_PASSWORD, stable_id

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    url = os.environ["DATABASE_URL"]
    assert_safe_test_database(url)
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    engine.dispose()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient, identifier: str, password: str = DEMO_PASSWORD) -> dict:
    response = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_and_seeded_login(client: TestClient):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["status"] == "ready"
    maria = _login(client, "45821367")
    assert maria["requires_otp"] is False
    me = client.get("/api/v1/me", headers=_auth(maria["access_token"]))
    assert me.status_code == 200
    body = me.json()
    assert body["full_name"] == "María Elena Quispe Huanca"
    assert "totp_secret" not in body
    assert body["phone_masked"].endswith("763")
    accounts = client.get("/api/v1/accounts", headers=_auth(maria["access_token"])).json()
    ahorro = next(item for item in accounts if item["number"] == "00110000004821")
    assert ahorro["available_balance"] == "11647.45"
    assert ahorro["cci"] == "99900110000004821044"
    assert ahorro["number_masked"].endswith("4821")
    movements = client.get(f"/api/v1/accounts/{ahorro['id']}/movements", headers=_auth(maria["access_token"])).json()
    assert movements["total"] >= 10
    assert movements["items"][0]["occurred_at"].startswith("2026-11-24")


def test_carlos_needs_the_authenticator(client: TestClient):
    pending = _login(client, "carlos.mendoza@correo.pe")
    assert pending["requires_otp"] is True
    assert pending["access_token"] is None
    wrong = client.post("/api/v1/auth/otp", json={"challenge_token": pending["challenge_token"], "code": "000000"})
    assert wrong.status_code == 401
    assert wrong.json()["code"] == "OTP_INVALID"
    code = pyotp.TOTP(CARLOS_TOTP_SECRET).now()
    ok = client.post("/api/v1/auth/otp", json={"challenge_token": pending["challenge_token"], "code": code})
    assert ok.status_code == 200
    assert ok.json()["access_token"]


def test_blocked_user_and_bad_password_do_not_share_a_body(client: TestClient):
    blocked = client.post("/api/v1/auth/login", json={"identifier": "33445566", "password": DEMO_PASSWORD})
    assert blocked.status_code == 403
    assert blocked.json()["code"] == "USER_BLOCKED"
    missing = client.post("/api/v1/auth/login", json={"identifier": "99999999", "password": "Clave.2026"})
    assert missing.status_code == 401
    assert missing.json()["message"] == "Credenciales inválidas."
    bad = client.post("/api/v1/auth/login", json={"identifier": "45821367", "password": "Clave.2026"})
    assert bad.status_code == 401


def test_register_validates_and_opens_a_zero_balance_account(client: TestClient):
    invalid = client.post(
        "/api/v1/auth/register",
        json={
            "dni": "12",
            "email": "no",
            "phone": "123",
            "given_names": "A",
            "paternal_surname": "B",
            "maternal_surname": "C",
            "password": "abc",
        },
    )
    assert invalid.status_code == 422
    assert len(invalid.json()["details"]) >= 5
    created = client.post(
        "/api/v1/auth/register",
        json={
            "dni": "55667788",
            "email": "nuevo.alumno@correo.pe",
            "phone": "987654321",
            "given_names": "Ana Lucía",
            "paternal_surname": "Flores",
            "maternal_surname": "Quispe",
            "password": "Clave.2026",
        },
    )
    assert created.status_code == 201, created.text
    token = created.json()["access_token"]
    accounts = client.get("/api/v1/accounts", headers=_auth(token)).json()
    assert len(accounts) == 1
    assert accounts[0]["available_balance"] == "0.00"
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "dni": "55667788",
            "email": "otro.alumno@correo.pe",
            "phone": "987654322",
            "given_names": "Ana Lucía",
            "paternal_surname": "Flores",
            "maternal_surname": "Quispe",
            "password": "Clave.2026",
        },
    )
    assert duplicate.status_code == 409


def test_internal_transfer_external_fee_and_cts_block(client: TestClient):
    maria = _login(client, "45821367")
    headers = _auth(maria["access_token"])
    accounts = client.get("/api/v1/accounts", headers=headers).json()
    ahorro = next(item for item in accounts if item["product_type"] == "ahorro")
    corriente = next(item for item in accounts if item["product_type"] == "corriente")
    cts = next(item for item in accounts if item["product_type"] == "cts")
    carlos_login = client.post("/api/v1/auth/login", json={"identifier": "70129458", "password": DEMO_PASSWORD}).json()
    carlos_token = client.post(
        "/api/v1/auth/otp",
        json={"challenge_token": carlos_login["challenge_token"], "code": pyotp.TOTP(CARLOS_TOTP_SECRET).now()},
    ).json()["access_token"]
    carlos_accounts = client.get("/api/v1/accounts", headers=_auth(carlos_token)).json()
    carlos_ahorro = next(item for item in carlos_accounts if item["number"] == "00110000007751")
    opening_carlos = carlos_ahorro["available_balance"]
    sent = client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "origin_account_id": ahorro["id"],
            "destination_account_number": "00110000007751",
            "amount": "25.50",
            "concept": "Almuerzo del viernes",
        },
    )
    assert sent.status_code == 201, sent.text
    body = sent.json()
    assert body["commission"] == "0.00"
    assert body["status"] == "completada"
    assert body["operation_code"].startswith("AB-")
    updated = client.get(f"/api/v1/accounts/{carlos_ahorro['id']}", headers=_auth(carlos_token)).json()
    assert round(float(updated["available_balance"]) - float(opening_carlos), 2) == 25.50
    own = client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "origin_account_id": ahorro["id"],
            "destination_account_number": ahorro["number"],
            "amount": "10.00",
            "concept": "A mí mismo",
        },
    )
    assert own.status_code == 409
    assert own.json()["code"] == "SAME_ACCOUNT"
    external = client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "origin_account_id": corriente["id"],
            "destination_cci": "99800112345678901234",
            "destination_holder": "Inversiones Colchane",
            "amount": "40.00",
            "concept": "Factura 1844",
        },
    )
    assert external.status_code == 201, external.text
    assert external.json()["commission"] == "4.50"
    assert external.json()["status"] == "enviada"
    cts_try = client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "origin_account_id": cts["id"],
            "destination_account_number": ahorro["number"],
            "amount": "10.00",
            "concept": "Retiro CTS",
        },
    )
    assert cts_try.status_code == 409
    assert cts_try.json()["code"] == "CTS_RESTRICTED"
    poor = _login(client, "41290873")
    lucia_accounts = client.get("/api/v1/accounts", headers=_auth(poor["access_token"])).json()
    too_much = client.post(
        "/api/v1/transfers",
        headers=_auth(poor["access_token"]),
        json={
            "origin_account_id": lucia_accounts[0]["id"],
            "destination_account_number": "00110000004821",
            "amount": "500.00",
            "concept": "No alcanza",
        },
    )
    assert too_much.status_code == 409
    assert too_much.json()["code"] == "INSUFFICIENT_FUNDS"


def test_payment_card_branch_and_totp_setup(client: TestClient):
    maria = _login(client, "45821367")
    headers = _auth(maria["access_token"])
    accounts = client.get("/api/v1/accounts", headers=headers).json()
    corriente = next(item for item in accounts if item["product_type"] == "corriente")
    catalog = client.get("/api/v1/payments/services", headers=headers).json()
    assert any(item["code"] == "UPTSERV" for item in catalog)
    paid = client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "origin_account_id": corriente["id"],
            "service_code": "UPTSERV",
            "reference": "20240018",
            "amount": "15.00",
        },
    )
    assert paid.status_code == 201, paid.text
    bad_ref = client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "origin_account_id": corriente["id"],
            "service_code": "MOVIL-SUR",
            "reference": "123",
            "amount": "10.00",
        },
    )
    assert bad_ref.status_code == 422
    cards = client.get("/api/v1/cards", headers=headers).json()
    assert all("pan" not in card or card["pan_masked"].startswith("••••") for card in cards)
    visa = next(card for card in cards if card["last4"] == "4412")
    blocked = client.post(f"/api/v1/cards/{visa['id']}/block", headers=headers)
    assert blocked.json()["status"] == "blocked"
    again = client.post(f"/api/v1/cards/{visa['id']}/block", headers=headers)
    assert again.status_code == 409
    client.post(f"/api/v1/cards/{visa['id']}/unblock", headers=headers)
    branches = client.get("/api/v1/branches", headers=headers, params={"latitude": -18.014, "longitude": -70.254}).json()
    assert branches[0]["distance_km"] < branches[-1]["distance_km"]
    setup = client.post("/api/v1/security/totp/setup", headers=headers).json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/AndesBank")
    code = pyotp.TOTP(setup["secret"]).now()
    assert client.post("/api/v1/security/totp/confirm", headers=headers, json={"code": code}).status_code == 204
    profile = client.get("/api/v1/me", headers=headers).json()
    assert profile["totp_enabled"] is True
    assert stable_id("user-maria") == profile["id"]
