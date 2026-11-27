from __future__ import annotations

BANK_CODE = "999"
ACCOUNT_LENGTH = 14
CCI_LENGTH = 20


def checksum(body: str) -> str:
    total = sum(int(digit) for digit in body)
    return f"{total % 97:02d}"


def build_cci(account_number: str) -> str:
    if len(account_number) != ACCOUNT_LENGTH or not account_number.isdigit():
        raise ValueError("La cuenta interna debe tener 14 dígitos.")
    # 3 del banco + 14 de la cuenta + 1 de relleno = 18. Los dos últimos son el control.
    body = f"{BANK_CODE}{account_number}0"
    return body + checksum(body)


def cci_is_ours(cci: str) -> bool:
    return len(cci) == CCI_LENGTH and cci.isdigit() and cci.startswith(BANK_CODE)


def cci_checksum_ok(cci: str) -> bool:
    if not cci_is_ours(cci):
        return False
    body, control = cci[:18], cci[18:]
    return checksum(body) == control
