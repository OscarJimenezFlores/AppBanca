from __future__ import annotations


def mask_keep_last(value: str, visible: int, bullet: str = "•") -> str:
    if visible < 0:
        raise ValueError("visible no puede ser negativo")
    if len(value) <= visible:
        return bullet * len(value)
    hidden = len(value) - visible
    return (bullet * hidden) + value[-visible:]


def mask_account(number: str) -> str:
    return mask_keep_last(number, 4)


def mask_cci(cci: str) -> str:
    return mask_keep_last(cci, 4)


def mask_phone(phone: str) -> str:
    return mask_keep_last(phone, 3)


def group_cci(cci: str) -> str:
    return " ".join(cci[index : index + 4] for index in range(0, len(cci), 4))


def group_account(number: str) -> str:
    if len(number) != 14:
        return number
    return f"{number[0:4]} {number[4:8]} {number[8:12]} {number[12:14]}"
