#!/usr/bin/env python3
"""Resolve the latest completed 14-day reporting period."""

from __future__ import annotations

import argparse
from datetime import date, timedelta


ANCHOR_START = date(2026, 7, 6)
PERIOD_DAYS = 14


def latest_complete_period(as_of: date) -> tuple[date, date]:
    """Return the latest anchor-aligned period whose end is before as_of."""

    cycle = (as_of - ANCHOR_START).days // PERIOD_DAYS
    start = ANCHOR_START + timedelta(days=cycle * PERIOD_DAYS)
    end = start + timedelta(days=PERIOD_DAYS - 1)
    if end >= as_of:
        start -= timedelta(days=PERIOD_DAYS)
        end -= timedelta(days=PERIOD_DAYS)
    return start, end


def format_period(start: date, end: date) -> str:
    return f"{start:%Y.%m.%d}-{end:%Y.%m.%d}"


def main():
    parser = argparse.ArgumentParser(description="计算最近完整教育行业双周区间")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    print(format_period(*latest_complete_period(args.as_of)))


if __name__ == "__main__":
    main()
