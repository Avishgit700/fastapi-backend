# app/utils/dates.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

KNOWN_FORMATS = (
    "%d/%m/%Y",
    "%d/%m/%Y, %H:%M",
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M",
)

def parse_any_dt(value: Optional[str | datetime]) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()

    # ISO first (handles “...T...Z” too)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        pass

    for fmt in KNOWN_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None
