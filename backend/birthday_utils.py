"""Следующий календарный день рождения и число дней до него."""

from __future__ import annotations

import datetime as dt


def next_birthday_date(birth: dt.date, today: dt.date | None = None) -> dt.date:
    """Календарная дата ближайшего дня рождения (год — тот, когда ДР наступит следующим)."""
    today = today or dt.date.today()
    y = today.year
    try:
        this_year = dt.date(y, birth.month, birth.day)
    except ValueError:
        this_year = dt.date(y, 2, 28)
    if this_year < today:
        y += 1
        try:
            return dt.date(y, birth.month, birth.day)
        except ValueError:
            return dt.date(y, 2, 28)
    return this_year


def days_until_next_birthday(birth: dt.date, today: dt.date | None = None) -> int:
    """Дней до ближайшего наступления month/day из даты рождения (29 фев → 28 фев в невисокосные годы)."""
    today = today or dt.date.today()
    nxt = next_birthday_date(birth, today)
    return (nxt - today).days
