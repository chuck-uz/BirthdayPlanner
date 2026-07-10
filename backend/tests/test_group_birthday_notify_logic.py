import datetime as dt

from group_birthday_notify_logic import (
    SINGLE_ADMIN_FALLBACK_LEAD_DAYS,
    plan_group_birthday_notifications,
)
from models import Group, GroupRole, User, UserGroup

TODAY = dt.date(2026, 1, 1)
ADMIN_LEAD_DAYS = 7


def _user(id_: int, *, birth_date: dt.date | None, full_name: str = "U", is_blocked: bool = False) -> User:
    u = User(telegram_id=id_, full_name=full_name, birth_date=birth_date, is_blocked=is_blocked)
    u.id = id_
    return u


def _membership(user: User, role: str) -> UserGroup:
    m = UserGroup(user_id=user.id, group_id=1, role=role)
    m.user = user
    return m


def _group() -> Group:
    g = Group(name="Test Group")
    g.id = 1
    return g


def _birth_date_in_days(days: int, today: dt.date = TODAY) -> dt.date:
    target = today + dt.timedelta(days=days)
    return dt.date(1990, target.month, target.day)


def test_member_birthday_notifies_all_admins_at_lead_days():
    admin1 = _user(1, birth_date=None, full_name="Admin One")
    admin2 = _user(2, birth_date=None, full_name="Admin Two")
    birthday_member = _user(3, birth_date=_birth_date_in_days(ADMIN_LEAD_DAYS), full_name="Member")
    memberships = [
        _membership(admin1, GroupRole.admin.value),
        _membership(admin2, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert len(plans) == 1
    assert plans[0].notification_kind == "notify_admins"
    assert set(plans[0].recipient_user_ids) == {1, 2}


def test_admin_birthday_with_other_admins_notifies_other_admins_only():
    birthday_admin = _user(1, birth_date=_birth_date_in_days(ADMIN_LEAD_DAYS), full_name="Admin")
    other_admin = _user(2, birth_date=None, full_name="Other Admin")
    member = _user(3, birth_date=None, full_name="Member")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(other_admin, GroupRole.admin.value),
        _membership(member, GroupRole.member.value),
    ]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert len(plans) == 1
    assert plans[0].notification_kind == "notify_admins"
    assert plans[0].recipient_user_ids == (2,)


def test_single_admin_birthday_falls_back_to_members_at_seven_days():
    birthday_admin = _user(
        1, birth_date=_birth_date_in_days(SINGLE_ADMIN_FALLBACK_LEAD_DAYS), full_name="Sole Admin"
    )
    member1 = _user(2, birth_date=None, full_name="Member One")
    member2 = _user(3, birth_date=None, full_name="Member Two")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(member1, GroupRole.member.value),
        _membership(member2, GroupRole.member.value),
    ]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert len(plans) == 1
    assert plans[0].notification_kind == "notify_members_fallback"
    assert set(plans[0].recipient_user_ids) == {2, 3}


def test_single_admin_birthday_does_not_fire_at_admin_lead_days():
    """7-дневный fallback не путается с настраиваемым admin_lead_days, если они различаются."""
    other_lead_days = 10
    birthday_admin = _user(1, birth_date=_birth_date_in_days(other_lead_days), full_name="Sole Admin")
    member = _user(2, birth_date=None, full_name="Member")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(member, GroupRole.member.value),
    ]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        admin_lead_days=other_lead_days,  # отличается от SINGLE_ADMIN_FALLBACK_LEAD_DAYS=7
    )

    # single-admin fallback триггерится только ровно на 7-й день, а не на admin_lead_days.
    assert plans == []


def test_single_admin_alone_in_group_produces_no_plan():
    birthday_admin = _user(
        1, birth_date=_birth_date_in_days(SINGLE_ADMIN_FALLBACK_LEAD_DAYS), full_name="Sole Admin"
    )
    memberships = [_membership(birthday_admin, GroupRole.admin.value)]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert plans == []


def test_wrong_lead_day_produces_no_plan():
    admin = _user(1, birth_date=None, full_name="Admin")
    birthday_member = _user(2, birth_date=_birth_date_in_days(ADMIN_LEAD_DAYS + 1), full_name="Member")
    memberships = [
        _membership(admin, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert plans == []


def test_blocked_birthday_user_produces_no_plan():
    admin = _user(1, birth_date=None, full_name="Admin")
    birthday_member = _user(
        2, birth_date=_birth_date_in_days(ADMIN_LEAD_DAYS), full_name="Member", is_blocked=True
    )
    memberships = [
        _membership(admin, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert plans == []


def test_birthday_user_not_a_member_produces_no_plan():
    admin = _user(1, birth_date=None, full_name="Admin")
    outsider = _user(2, birth_date=_birth_date_in_days(ADMIN_LEAD_DAYS), full_name="Outsider")
    memberships = [_membership(admin, GroupRole.admin.value)]

    plans = plan_group_birthday_notifications(
        group=_group(),
        memberships=memberships,
        birthday_user=outsider,
        today=TODAY,
        admin_lead_days=ADMIN_LEAD_DAYS,
    )

    assert plans == []
