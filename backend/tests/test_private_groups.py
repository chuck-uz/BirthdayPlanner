import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models import GroupRole
from services.private_groups import (
    PrivateGroupError,
    create_group,
    get_active_invite,
    get_group_detail,
    join_group_by_invite_token,
    promote_member_to_admin,
    regenerate_invite_token,
    update_group_settings,
)


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
