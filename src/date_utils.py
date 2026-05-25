from __future__ import annotations

import datetime as dt


def parse_date(date_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(date_str)[:10])
    except (ValueError, TypeError):
        return dt.date(1970, 1, 1)


def to_atom_date(date_str: str) -> str:
    d = parse_date(date_str)
    return f"{d.isoformat()}T00:00:00Z"
