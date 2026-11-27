from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def operation_code(now: datetime) -> str:
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%d")
    return f"AB-{stamp}-{uuid4().hex[:8].upper()}"
