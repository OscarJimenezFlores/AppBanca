from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

LIMA = timezone(timedelta(hours=-5))


def as_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ValueError("la fecha debe traer zona horaria")
    return moment.astimezone(timezone.utc)


def lima_day(moment: datetime) -> date:
    return as_utc(moment).astimezone(LIMA).date()


def lima_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day, tzinfo=LIMA)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)
