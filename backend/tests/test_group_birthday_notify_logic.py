import datetime as dt

from group_birthday_notify_logic import plan_group_birthday_prompt
from models import Group, GroupRole, User, UserGroup

TODAY = dt.date(2026, 1, 1)
LEAD_DAYS = 7


def _user(id_: int, *, birth_date: dt.date | None, full_name: str = "U", is_blocked: bool = False) -> User:
    u = User(telegram_id=id_, full_name=full_name, birth_date=birth_date, is_blocked=is_blocked)
    u.id = id_
    return u


def _membership(user: User, role: str) -> UserGroup:
    m = UserGroup(user_id=user.id, group_id=1, role=role)
    m.user = user
    return m


def _group(notify_lead_days: int = LEAD_DAYS) -> Group:
    g = Group(name="Test Group", notify_lead_days=notify_lead_days)
    g.id = 1
    return g


def _birth_date_in_days(days: int, today: dt.date = TODAY) -> dt.date:
    target = today + dt.timedelta(days=days)
    return dt.date(1990, target.month, target.day)


def test_member_birthday_with_subscribers_notifies_all_admins():
    admin1 = _user(1, birth_date=None, full_name="Admin One")
    admin2 = _user(2, birth_date=None, full_name="Admin Two")
    birthday_member = _user(3, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Member")
    memberships = [
        _membership(admin1, GroupRole.admin.value),
        _membership(admin2, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        has_subscribers=True,
    )

    assert candidate is not None
    assert set(candidate.recipient_user_ids) == {1, 2}


def test_member_birthday_without_subscribers_produces_no_prompt():
    admin = _user(1, birth_date=None, full_name="Admin")
    birthday_member = _user(2, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Member")
    memberships = [
        _membership(admin, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        has_subscribers=False,
    )

    assert candidate is None


def test_admin_birthday_with_other_admins_and_subscribers_notifies_other_admins():
    birthday_admin = _user(1, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Admin")
    other_admin = _user(2, birth_date=None, full_name="Other Admin")
    member = _user(3, birth_date=None, full_name="Member")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(other_admin, GroupRole.admin.value),
        _membership(member, GroupRole.member.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        has_subscribers=True,
    )

    assert candidate is not None
    assert candidate.recipient_user_ids == (2,)


def test_admin_birthday_with_other_admins_but_no_subscribers_produces_no_prompt():
    birthday_admin = _user(1, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Admin")
    other_admin = _user(2, birth_date=None, full_name="Other Admin")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(other_admin, GroupRole.admin.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        has_subscribers=False,
    )

    assert candidate is None


def test_single_admin_birthday_falls_back_to_all_members_even_without_subscribers():
    """Единственный админ группы: промпт уходит всем остальным всегда, независимо от подписчиков."""
    birthday_admin = _user(1, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Sole Admin")
    member1 = _user(2, birth_date=None, full_name="Member One")
    member2 = _user(3, birth_date=None, full_name="Member Two")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(member1, GroupRole.member.value),
        _membership(member2, GroupRole.member.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        has_subscribers=False,
    )

    assert candidate is not None
    assert set(candidate.recipient_user_ids) == {2, 3}


def test_single_admin_birthday_falls_back_to_all_members_with_subscribers_too():
    birthday_admin = _user(1, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Sole Admin")
    member = _user(2, birth_date=None, full_name="Member")
    memberships = [
        _membership(birthday_admin, GroupRole.admin.value),
        _membership(member, GroupRole.member.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        has_subscribers=True,
    )

    assert candidate is not None
    assert candidate.recipient_user_ids == (2,)


def test_single_admin_alone_in_group_produces_no_prompt():
    birthday_admin = _user(1, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Sole Admin")
    memberships = [_membership(birthday_admin, GroupRole.admin.value)]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_admin,
        today=TODAY,
        has_subscribers=False,
    )

    assert candidate is None


def test_uses_group_specific_lead_days():
    admin = _user(1, birth_date=None, full_name="Admin")
    birthday_member = _user(2, birth_date=_birth_date_in_days(20), full_name="Member")
    memberships = [
        _membership(admin, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    # Группа с lead_days=7 не сработает на 20-дневный горизонт.
    assert (
        plan_group_birthday_prompt(
            group=_group(notify_lead_days=7),
            memberships=memberships,
            birthday_user=birthday_member,
            today=TODAY,
            has_subscribers=True,
        )
        is None
    )

    # А группа с lead_days=20 — сработает.
    candidate = plan_group_birthday_prompt(
        group=_group(notify_lead_days=20),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        has_subscribers=True,
    )
    assert candidate is not None
    assert candidate.days_left == 20


def test_blocked_birthday_user_produces_no_prompt():
    admin = _user(1, birth_date=None, full_name="Admin")
    birthday_member = _user(
        2, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Member", is_blocked=True
    )
    memberships = [
        _membership(admin, GroupRole.admin.value),
        _membership(birthday_member, GroupRole.member.value),
    ]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=birthday_member,
        today=TODAY,
        has_subscribers=True,
    )

    assert candidate is None


def test_birthday_user_not_a_member_produces_no_prompt():
    admin = _user(1, birth_date=None, full_name="Admin")
    outsider = _user(2, birth_date=_birth_date_in_days(LEAD_DAYS), full_name="Outsider")
    memberships = [_membership(admin, GroupRole.admin.value)]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=outsider,
        today=TODAY,
        has_subscribers=True,
    )

    assert candidate is None


def test_no_birth_date_produces_no_prompt():
    admin = _user(1, birth_date=None, full_name="Admin")
    memberships = [_membership(admin, GroupRole.admin.value)]

    candidate = plan_group_birthday_prompt(
        group=_group(),
        memberships=memberships,
        birthday_user=admin,
        today=TODAY,
        has_subscribers=True,
    )

    assert candidate is None
