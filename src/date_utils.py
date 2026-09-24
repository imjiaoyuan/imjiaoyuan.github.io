from __future__ import annotations

import datetime as dt
import sys


def parse_date(date_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(date_str)[:10])
    except ValueError:
        print(f"Warning: Invalid date format '{date_str}', using 1970-01-01 as fallback.", file=sys.stderr)
        return dt.date(1970, 1, 1)
    except TypeError:
        print(f"Warning: Date value is not a string: {date_str!r}, using 1970-01-01 as fallback.", file=sys.stderr)
        return dt.date(1970, 1, 1)
