from __future__ import annotations

from decimal import Decimal

from app.domain.money import money
from app.types.entities import PostedLine, StoryLine


def post_story(opening: Decimal, lines: list[StoryLine]) -> tuple[Decimal, list[PostedLine]]:
    balance = money(opening)
    posted: list[PostedLine] = []
    ordered = sorted(lines, key=lambda line: line.occurred_at)
    for line in ordered:
        amount = money(line.amount)
        if amount <= 0:
            raise ValueError("un movimiento de la historia tiene monto no positivo")
        if line.direction == "credit":
            balance = money(balance + amount)
        elif line.direction == "debit":
            balance = money(balance - amount)
        else:
            raise ValueError("dirección desconocida")
        if balance < 0:
            raise ValueError("la historia deja la cuenta en negativo")
        posted.append(
            PostedLine(
                occurred_at=line.occurred_at,
                direction=line.direction,
                amount=amount,
                concept=line.concept,
                counterparty_name=line.counterparty_name,
                counterparty_account=line.counterparty_account,
                channel=line.channel,
                balance_after=balance,
            )
        )
    return balance, posted
