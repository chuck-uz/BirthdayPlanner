"""Следующий календарный день рождения и число дней до него."""

from __future__ import annotations

import datetime as dt


def days_until_next_birthday(birth: dt.date, today: dt.date | None = None) -> int:
    """Дней до ближайшего наступления month/day из даты рождения (29 фев → 28 фев в невисокосные годы)."""
    today = today or dt.date.today()
    y = today.year
    try:
        this_year = dt.date(y, birth.month, birth.day)
    except ValueError:
        this_year = dt.date(y, 2, 28)
    if this_year < today:
        y += 1
        try:
            nxt = dt.date(y, birth.month, birth.day)
        except ValueError:
            nxt = dt.date(y, 2, 28)
    else:
        nxt = this_year
    return (nxt - today).days
