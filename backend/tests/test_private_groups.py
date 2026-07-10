import datetime as dt

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models import GroupRole
from services.private_groups import (
    PrivateGroupError,
    create_group,
    get_active_invite,
    get_group_detail,
    join_group_by_invite_token,
    list_group_birthdays,
    promote_member_to_admin,
    regenerate_invite_token,
    update_group_settings,
)

BIRTHDAYS_TODAY = dt.date(2026, 1, 1)


def _birth_date_in_days(days: int, today: dt.date = BIRTHDAYS_TODAY) -> dt.date:
    target = today + dt.timedelta(days=days)
    return dt.date(1990, target.month, target.day)


async def test_create_group_makes_creator_admin(db_session: AsyncSession, make_user):
    creator = await make_user()
    group, membership, invite = await create_group(db_session, creator=creator, name="  Family  ")

    assert group.name == "Family"
    assert membership.role == GroupRole.admin.value
    assert invite.group_id == group.id
    assert invite.revoked_at is None


async def test_create_group_rejects_blank_name(db_session: AsyncSession, make_user):
    creator = await make_user()
    with pytest.raises(PrivateGroupError) as exc:
        await create_group(db_session, creator=creator, name="   ")
    assert exc.value.code == "invalid_name"


async def test_join_by_invite_token_adds_member(db_session: AsyncSession, make_user):
    creator = await make_user()
    joiner = await make_user()
    group, _, invite = await create_group(db_session, creator=creator, name="Friends")

    joined_group, membership = await join_group_by_invite_token(
        db_session, user=joiner, invite_token=invite.token
    )

    assert joined_group.id == group.id
    assert membership.role == GroupRole.member.value


async def test_join_is_idempotent_for_existing_member(db_session: AsyncSession, make_user):
    creator = await make_user()
    joiner = await make_user()
    _, _, invite = await create_group(db_session, creator=creator, name="Friends")

    _, first = await join_group_by_invite_token(db_session, user=joiner, invite_token=invite.token)
    _, second = await join_group_by_invite_token(db_session, user=joiner, invite_token=invite.token)

    assert first.id == second.id
    assert second.role == GroupRole.member.value


async def test_join_with_unknown_token_raises(db_session: AsyncSession, make_user):
    joiner = await make_user()
    with pytest.raises(PrivateGroupError) as exc:
        await join_group_by_invite_token(db_session, user=joiner, invite_token="does-not-exist")
    assert exc.value.code == "group_not_found"


async def test_join_with_revoked_token_raises(db_session: AsyncSession, make_user):
    creator = await make_user()
    joiner = await make_user()
    group, _, old_invite = await create_group(db_session, creator=creator, name="Friends")
    await regenerate_invite_token(db_session, group_id=group.id, actor=creator)

    with pytest.raises(PrivateGroupError) as exc:
        await join_group_by_invite_token(db_session, user=joiner, invite_token=old_invite.token)
    assert exc.value.code == "group_not_found"


async def test_regenerate_invite_requires_admin(db_session: AsyncSession, make_user):
    creator = await make_user()
    member = await make_user()
    group, _, invite = await create_group(db_session, creator=creator, name="Friends")
    await join_group_by_invite_token(db_session, user=member, invite_token=invite.token)

    with pytest.raises(PrivateGroupError) as exc:
        await regenerate_invite_token(db_session, group_id=group.id, actor=member)
    assert exc.value.code == "admin_required"


async def test_regenerate_invite_revokes_old_and_issues_new(db_session: AsyncSession, make_user):
    creator = await make_user()
    group, _, old_invite = await create_group(db_session, creator=creator, name="Friends")

    new_invite = await regenerate_invite_token(db_session, group_id=group.id, actor=creator)

    assert new_invite.token != old_invite.token
    active = await get_active_invite(db_session, group_id=group.id)
    assert active is not None
    assert active.id == new_invite.id


async def test_promote_member_to_admin(db_session: AsyncSession, make_user):
    creator = await make_user()
    member = await make_user()
    group, _, invite = await create_group(db_session, creator=creator, name="Friends")
    await join_group_by_invite_token(db_session, user=member, invite_token=invite.token)

    promoted = await promote_member_to_admin(
        db_session, group_id=group.id, actor=creator, target_user_id=member.id
    )
    assert promoted.role == GroupRole.admin.value


async def test_promote_is_idempotent_for_existing_admin(db_session: AsyncSession, make_user):
    creator = await make_user()
    group, membership, _ = await create_group(db_session, creator=creator, name="Friends")

    result = await promote_member_to_admin(
        db_session, group_id=group.id, actor=creator, target_user_id=creator.id
    )
    assert result.id == membership.id
    assert result.role == GroupRole.admin.value


async def test_promote_requires_admin_actor(db_session: AsyncSession, make_user):
    creator = await make_user()
    member_a = await make_user()
    member_b = await make_user()
    group, _, invite = await create_group(db_session, creator=creator, name="Friends")
    await join_group_by_invite_token(db_session, user=member_a, invite_token=invite.token)
    await join_group_by_invite_token(db_session, user=member_b, invite_token=invite.token)

    with pytest.raises(PrivateGroupError) as exc:
        await promote_member_to_admin(
            db_session, group_id=group.id, actor=member_a, target_user_id=member_b.id
        )
    assert exc.value.code == "admin_required"


async def test_promote_target_must_be_member(db_session: AsyncSession, make_user):
    creator = await make_user()
    outsider = await make_user()
    group, _, _ = await create_group(db_session, creator=creator, name="Friends")

    with pytest.raises(PrivateGroupError) as exc:
        await promote_member_to_admin(
            db_session, group_id=group.id, actor=creator, target_user_id=outsider.id
        )
    assert exc.value.code == "target_not_member"


async def test_get_group_detail_requires_membership(db_session: AsyncSession, make_user):
    creator = await make_user()
    outsider = await make_user()
    group, _, _ = await create_group(db_session, creator=creator, name="Friends")

    with pytest.raises(PrivateGroupError) as exc:
        await get_group_detail(db_session, group_id=group.id, user=outsider)
    assert exc.value.code == "not_a_member"


async def test_update_group_settings_toggles_invite_visibility(db_session: AsyncSession, make_user):
    creator = await make_user()
    group, _, _ = await create_group(db_session, creator=creator, name="Friends")
    assert group.invite_visible_to_members is False

    updated = await update_group_settings(
        db_session, group_id=group.id, actor=creator, invite_visible_to_members=True
    )
    assert updated.invite_visible_to_members is True


async def test_list_group_birthdays_excludes_own_birthday(db_session: AsyncSession, make_user):
    creator = await make_user(birth_date=_birth_date_in_days(5))
    await create_group(db_session, creator=creator, name="Solo")

    sections = await list_group_birthdays(db_session, user=creator, today=BIRTHDAYS_TODAY)
    assert sections == []


async def test_list_group_birthdays_sorted_within_group(db_session: AsyncSession, make_user):
    creator = await make_user(birth_date=None)
    far = await make_user(full_name="Far", birth_date=_birth_date_in_days(20))
    near = await make_user(full_name="Near", birth_date=_birth_date_in_days(3))
    group, _, invite = await create_group(db_session, creator=creator, name="Friends")
    await join_group_by_invite_token(db_session, user=far, invite_token=invite.token)
    await join_group_by_invite_token(db_session, user=near, invite_token=invite.token)

    sections = await list_group_birthdays(db_session, user=creator, today=BIRTHDAYS_TODAY)
    assert len(sections) == 1
    group_out, members = sections[0]
    assert group_out.id == group.id
    assert [m[0].id for m in members] == [near.id, far.id]
    assert [m[1] for m in members] == [3, 20]


async def test_list_group_birthdays_groups_sorted_by_soonest_member(
    db_session: AsyncSession, make_user
):
    creator = await make_user(birth_date=None)
    a = await make_user(full_name="A", birth_date=_birth_date_in_days(10))
    b = await make_user(full_name="B", birth_date=_birth_date_in_days(2))
    group_far, _, invite_far = await create_group(db_session, creator=creator, name="Far Group")
    await join_group_by_invite_token(db_session, user=a, invite_token=invite_far.token)
    group_near, _, invite_near = await create_group(db_session, creator=creator, name="Near Group")
    await join_group_by_invite_token(db_session, user=b, invite_token=invite_near.token)

    sections = await list_group_birthdays(db_session, user=creator, today=BIRTHDAYS_TODAY)
    assert [g.id for g, _ in sections] == [group_near.id, group_far.id]


async def test_list_group_birthdays_omits_groups_without_dates(
    db_session: AsyncSession, make_user
):
    creator = await make_user(birth_date=None)
    no_bday = await make_user(full_name="No Bday", birth_date=None)
    group, _, invite = await create_group(db_session, creator=creator, name="Empty Dates")
    await join_group_by_invite_token(db_session, user=no_bday, invite_token=invite.token)

    sections = await list_group_birthdays(db_session, user=creator, today=BIRTHDAYS_TODAY)
    assert sections == []


async def test_list_group_birthdays_excludes_blocked_members(
    db_session: AsyncSession, make_user
):
    creator = await make_user(birth_date=None)
    blocked = await make_user(
        full_name="Blocked", birth_date=_birth_date_in_days(5), is_blocked=True
    )
    group, _, invite = await create_group(db_session, creator=creator, name="Group")
    await join_group_by_invite_token(db_session, user=blocked, invite_token=invite.token)

    sections = await list_group_birthdays(db_session, user=creator, today=BIRTHDAYS_TODAY)
    assert sections == []


async def test_list_group_birthdays_same_person_repeats_per_group(
    db_session: AsyncSession, make_user
):
    creator = await make_user(birth_date=None)
    friend = await make_user(full_name="Friend", birth_date=_birth_date_in_days(4))
    group1, _, invite1 = await create_group(db_session, creator=creator, name="Group One")
    await join_group_by_invite_token(db_session, user=friend, invite_token=invite1.token)
    group2, _, invite2 = await create_group(db_session, creator=creator, name="Group Two")
    await join_group_by_invite_token(db_session, user=friend, invite_token=invite2.token)

    sections = await list_group_birthdays(db_session, user=creator, today=BIRTHDAYS_TODAY)
    assert len(sections) == 2
    for _, members in sections:
        assert [m[0].id for m in members] == [friend.id]
