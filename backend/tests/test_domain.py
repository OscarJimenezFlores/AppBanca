from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.domain.access import assert_user_can_authenticate, note_failed_secret, note_successful_secret
from app.domain.calendar import lima_day, lima_day_bounds
from app.domain.cci import build_cci, cci_checksum_ok, cci_is_ours
from app.domain.errors import DomainError
from app.domain.geo import haversine_km
from app.domain.ledger import post_story
from app.domain.masking import group_account, group_cci, mask_account, mask_keep_last, mask_phone
from app.domain.money import money, money_str, parse_amount
from app.domain.policies import (
    DAILY_LIMIT,
    assert_amount_bounds,
    assert_can_debit,
    assert_daily_limit,
    assert_destination_operable,
    commission_for,
    needs_step_up,
)
from app.domain.validators import (
    account_number_error,
    cci_shape_error,
    concept_error,
    dni_error,
    email_error,
    name_error,
    otp_error,
    password_errors,
    phone_error,
)
from app.types.entities import Account, StoryLine, User


def _account(**kwargs) -> Account:
    base = dict(
        id="a",
        user_id="u",
        product_type="ahorro",
        number="00110000004821",
        cci=build_cci("00110000004821"),
        currency="PEN",
        available_balance=money("100.00"),
        status="active",
        alias="Ahorro",
        opened_on=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    base.update(kwargs)
    return Account(**base)


def _user(**kwargs) -> User:
    now = datetime(2026, 11, 26, tzinfo=timezone.utc)
    base = dict(
        id="u",
        dni="45821367",
        email="maria.quispe@correo.pe",
        phone="952418763",
        given_names="María Elena",
        paternal_surname="Quispe",
        maternal_surname="Huanca",
        password_hash="hash",
        totp_secret=None,
        totp_enabled=False,
        status="active",
        failed_attempts=0,
        locked_until=None,
        created_at=now,
    )
    base.update(kwargs)
    return User(**base)


def test_money_rejects_extra_decimals_and_keeps_two():
    assert money("10.50") == Decimal("10.50")
    assert money("10.5") == Decimal("10.50")
    assert money_str(money("10")) == "10.00"
    with pytest.raises(ValueError):
        money("10.555")
    with pytest.raises(ValueError):
        money("no")


@pytest.mark.parametrize(
    "raw",
    ["", " ", "1,500.00", "1500,50", "1e2", "+10", "-1", "00.50", ".50", "10.555", "S/ 10", "10 "],
)
def test_parse_amount_rejects_bank_unsafe_shapes(raw: str):
    with pytest.raises(ValueError):
        parse_amount(raw)


@pytest.mark.parametrize("raw, expected", [("1", "1.00"), ("1.2", "1.20"), ("10000.00", "10000.00"), ("0.01", "0.01")])
def test_parse_amount_accepts_plain_decimals(raw: str, expected: str):
    assert parse_amount(raw) == Decimal(expected)


def test_cci_vector_and_foreign_prefix():
    cci = build_cci("00110000004821")
    assert cci == "99900110000004821044"
    assert len(cci) == 20
    assert cci_is_ours(cci)
    assert cci_checksum_ok(cci)
    assert not cci_checksum_ok(cci[:-1] + "0")
    assert not cci_is_ours("99800112345678901234")
    with pytest.raises(ValueError):
        build_cci("123")


def test_masks_hide_everything_when_value_is_shorter_than_visible_tail():
    assert mask_account("00110000004821") == "••••••••••4821"
    assert mask_phone("952418763") == "••••••763"
    assert mask_keep_last("12", 4) == "••"
    assert group_account("00110000004821") == "0011 0000 0048 21"
    assert group_cci("99900110000004821044") == "9990 0110 0000 0482 1044"
    with pytest.raises(ValueError):
        mask_keep_last("1234", -1)


@pytest.mark.parametrize(
    "value, message",
    [("1234567", "8"), ("123456789", "8"), ("1234ABCD", "8"), ("00000000", "no es válido"), ("", "8")],
)
def test_dni_edges(value: str, message: str):
    assert message in (dni_error(value) or "")


def test_dni_phone_email_and_name_accept_demo_customer():
    assert dni_error("45821367") is None
    assert phone_error("952418763") is None
    assert phone_error("052418763") is not None
    assert phone_error("95241876") is not None
    assert email_error("maria.quispe@correo.pe") is None
    assert email_error("maria@correo") is not None
    assert email_error("a" * 150 + "@correo.pe") is not None
    assert name_error("María Elena", "Los nombres") is None
    assert name_error("A", "Los nombres") is not None
    assert name_error("Ana1", "Los nombres") is not None
    assert name_error("Ana\n", "Los nombres") is not None


def test_password_reports_every_broken_rule_at_once():
    errors = password_errors("abc")
    assert len(errors) >= 4
    assert password_errors("Andes.2026")
    assert password_errors("Clave.2026") == []
    assert password_errors("x" * 65)
    assert otp_error("12345")
    assert otp_error("12345a")
    assert otp_error("123456") is None
    assert account_number_error("00110000004821") is None
    assert account_number_error("0011000000482")
    assert cci_shape_error("99800112345678901234") is None
    assert concept_error("  Pago   alquiler  ") is None
    assert concept_error("")
    assert concept_error("x" * 81)
    assert concept_error("linea\nrota")


def test_debit_rules_cover_cts_funds_and_limits():
    cts = _account(product_type="cts", available_balance=money("5000.00"))
    with pytest.raises(DomainError) as blocked:
        assert_can_debit(cts, money("10.00"))
    assert blocked.value.code == "CTS_RESTRICTED"
    poor = _account(available_balance=money("5.00"))
    with pytest.raises(DomainError) as funds:
        assert_can_debit(poor, money("5.01"))
    assert funds.value.code == "INSUFFICIENT_FUNDS"
    stopped = _account(status="blocked")
    with pytest.raises(DomainError):
        assert_can_debit(stopped, money("1.00"))
    with pytest.raises(DomainError):
        assert_amount_bounds(money("0.50"), money("10000.00"), "una transferencia")
    with pytest.raises(DomainError):
        assert_amount_bounds(money("10000.01"), money("10000.00"), "una transferencia")
    assert_daily_limit(money("19999.00"), money("1.00"))
    with pytest.raises(DomainError) as daily:
        assert_daily_limit(DAILY_LIMIT, money("1.00"))
    assert daily.value.code == "DAILY_LIMIT"
    assert commission_for("internal") == Decimal("0.00")
    assert commission_for("external") == Decimal("4.50")
    assert needs_step_up(True, money("500.00"))
    assert not needs_step_up(True, money("499.99"))
    assert not needs_step_up(False, money("9000.00"))


def test_destination_cannot_be_the_same_account_or_a_cts():
    origin = _account()
    with pytest.raises(DomainError) as same:
        assert_destination_operable(origin, origin)
    assert same.value.code == "SAME_ACCOUNT"
    cts = _account(id="b", number="00110000001102", product_type="cts")
    with pytest.raises(DomainError):
        assert_destination_operable(cts, origin)


def test_ledger_is_ordered_and_refuses_overdraft():
    lines = [
        StoryLine(datetime(2026, 11, 2, tzinfo=timezone.utc), "debit", money("5.00"), "c", "n", "", "app"),
        StoryLine(datetime(2026, 11, 1, tzinfo=timezone.utc), "credit", money("10.00"), "a", "n", "", "app"),
    ]
    balance, posted = post_story(money("0.00"), lines)
    assert balance == Decimal("5.00")
    assert [item.balance_after for item in posted] == [Decimal("10.00"), Decimal("5.00")]
    with pytest.raises(ValueError):
        post_story(money("1.00"), [lines[0]])


def test_lima_calendar_has_no_daylight_saving_shift():
    moment = datetime(2026, 11, 26, 2, 30, tzinfo=timezone.utc)
    assert lima_day(moment).isoformat() == "2026-11-25"
    start, end = lima_day_bounds(lima_day(moment))
    assert start == datetime(2026, 11, 25, 5, 0, tzinfo=timezone.utc)
    assert end - start == timedelta(days=1)
    with pytest.raises(ValueError):
        lima_day(datetime(2026, 11, 26, 2, 30))


def test_lockout_trips_on_the_fifth_failure_and_clears_after_success():
    user = _user()
    now = datetime(2026, 11, 26, 15, tzinfo=timezone.utc)
    for _ in range(4):
        note_failed_secret(user, now)
    assert user.locked_until is None
    note_failed_secret(user, now)
    assert user.locked_until == now + timedelta(minutes=15)
    with pytest.raises(DomainError) as locked:
        assert_user_can_authenticate(user, now + timedelta(minutes=1))
    assert locked.value.code == "LOCKED"
    assert_user_can_authenticate(user, now + timedelta(minutes=15))
    note_successful_secret(user)
    assert user.failed_attempts == 0
    assert user.locked_until is None
    blocked = _user(status="blocked")
    with pytest.raises(DomainError) as denied:
        assert_user_can_authenticate(blocked, now)
    assert denied.value.code == "USER_BLOCKED"


def test_full_name_and_haversine_between_centro_and_pocollay():
    assert _user().full_name == "María Elena Quispe Huanca"
    distance = haversine_km(-18.01397, -70.25362, -17.99620, -70.21840)
    assert 4 < distance < 6
    with pytest.raises(ValueError):
        haversine_km(91, 0, 0, 0)
    with pytest.raises(ValueError):
        haversine_km(float("nan"), 0, 0, 0)
