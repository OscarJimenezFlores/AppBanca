from datetime import datetime, timedelta, timezone

import pyotp
import pytest

from app.dev.create_database import assert_safe_test_database, database_name
from app.infrastructure.config import Settings
from app.infrastructure.security import totp_matches


def test_database_guard_refuses_the_working_database():
    assert database_name("postgresql+psycopg://andes:andes_local@db:5432/andesbank_test") == "andesbank_test"
    assert_safe_test_database("postgresql://andes:x@db:5432/andesbank_test?sslmode=disable")
    with pytest.raises(RuntimeError):
        assert_safe_test_database("postgresql+psycopg://andes:x@db:5432/andesbank")
    with pytest.raises(RuntimeError):
        database_name("postgresql://andes:x@db:5432/andes-bank")


def test_settings_reject_a_short_secret():
    with pytest.raises(RuntimeError):
        Settings(database_url="postgresql+psycopg://a:b@db/andesbank", jwt_secret="corta").assert_usable()
    with pytest.raises(RuntimeError):
        Settings(database_url="sqlite:///local.db", jwt_secret="x" * 32).assert_usable()


def test_rfc6238_sha1_six_digits():
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    vectors = {
        59: "287082",
        1111111109: "081804",
        1111111111: "050471",
        1234567890: "005924",
        2000000000: "279037",
    }
    for stamp, code in vectors.items():
        moment = datetime.fromtimestamp(stamp, tz=timezone.utc)
        assert pyotp.TOTP(secret).at(stamp) == code
        assert totp_matches(secret, code, moment)
    moment = datetime.fromtimestamp(59, tz=timezone.utc)
    assert totp_matches(secret, "287082", moment + timedelta(seconds=30))
    assert not totp_matches(secret, "287082", moment + timedelta(seconds=90))
    assert not totp_matches(secret, "12345", moment)
    assert not totp_matches(secret, "000000", moment)
