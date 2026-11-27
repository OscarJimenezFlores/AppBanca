from __future__ import annotations

import os
import re

import psycopg


def database_name(url: str) -> str:
    name = url.rsplit("/", 1)[-1].split("?", 1)[0]
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise RuntimeError("El nombre de la base no es seguro para crearlo desde el entorno.")
    return name


def assert_safe_test_database(url: str) -> str:
    name = database_name(url)
    if not name.endswith("_test"):
        raise RuntimeError("La base de integración debe terminar en _test. No se borra la base de trabajo.")
    return name


def ensure_database(url: str) -> None:
    name = database_name(url)
    admin = url.rsplit("/", 1)[0] + "/andesbank"
    admin = admin.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(admin, autocommit=True) as connection:
        exists = connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if exists is None:
            connection.execute(f'CREATE DATABASE "{name}"')


if __name__ == "__main__":
    ensure_database(os.environ["DATABASE_URL"])
