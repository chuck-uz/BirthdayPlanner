import datetime as dt

from birthday_utils import days_until_next_birthday, next_birthday_date


def test_birthday_later_this_year():
    today = dt.date(2026, 1, 10)
    assert next_birthday_date(dt.date(2000, 6, 15), today) == dt.date(2026, 6, 15)
    assert days_until_next_birthday(dt.date(2000, 6, 15), today) == (dt.date(2026, 6, 15) - today).days


def test_birthday_already_passed_rolls_to_next_year():
    today = dt.date(2026, 7, 1)
    assert next_birthday_date(dt.date(1990, 6, 15), today) == dt.date(2027, 6, 15)


def test_birthday_today_is_zero_days():
    today = dt.date(2026, 6, 15)
    assert next_birthday_date(dt.date(1990, 6, 15), today) == today
    assert days_until_next_birthday(dt.date(1990, 6, 15), today) == 0


def test_leap_day_maps_to_feb_28_in_non_leap_year():
    # 2027 не високосный: 29 февраля отображается на 28 февраля.
    today = dt.date(2027, 1, 1)
    assert next_birthday_date(dt.date(2000, 2, 29), today) == dt.date(2027, 2, 28)


def test_leap_day_stays_feb_29_in_leap_year():
    today = dt.date(2028, 1, 1)  # 2028 високосный
    assert next_birthday_date(dt.date(2000, 2, 29), today) == dt.date(2028, 2, 29)
