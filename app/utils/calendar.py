from uuid import uuid4
from typing import List
from datetime import datetime, timedelta, timezone
from ..models import Todo

def _fmt(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def todos_to_ics(todos: List[Todo]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Todo+Time Manager//EN",
        "CALSCALE:GREGORIAN",
    ]
    for t in todos:
        if not t.due_date:
            continue
        uid = f"{t.id}-{uuid4()}@todo-time"
        status = "COMPLETED" if t.completed else "NEEDS-ACTION"
        lines += [
            "BEGIN:VTODO",
            f"UID:{uid}",
            f"DTSTAMP:{_fmt(t.created_at)}",
            f"DUE:{_fmt(t.due_date)}",
            f"SUMMARY:{t.title}",
            f"DESCRIPTION:{(t.notes or '').replace('\\n',' ')}",
            f"STATUS:{status}",
            "END:VTODO",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
