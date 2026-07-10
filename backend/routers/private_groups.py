from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import Group, GroupInvite, GroupRole, User, UserGroup
from ratelimit import limiter
from schemas.private_group import (
    GroupCreateIn,
    GroupDetailOut,
    GroupInviteOut,
    GroupJoinIn,
    GroupMemberOut,
    GroupOut,
    GroupSettingsUpdateIn,
)
from services.private_groups import (
    PrivateGroupError,
    create_group,
    get_group_detail,
    join_group_by_invite_token,
    list_user_groups,
    promote_member_to_admin,
    regenerate_invite_token,
    update_group_settings,
)

router = APIRouter(prefix="/api/groups", tags=["private-groups"])

_STATUS_MAP = {
    "group_not_found": status.HTTP_404_NOT_FOUND,
    "not_a_member": status.HTTP_404_NOT_FOUND,
    "target_not_member": status.HTTP_404_NOT_FOUND,
    "admin_required": status.HTTP_403_FORBIDDEN,
    "invalid_token": status.HTTP_400_BAD_REQUEST,
    "invalid_name": status.HTTP_400_BAD_REQUEST,
}


def _group_error_to_http(exc: PrivateGroupError) -> HTTPException:
    return HTTPException(
        status_code=_STATUS_MAP.get(exc.code, status.HTTP_400_BAD_REQUEST),
        detail=exc.code,
    )


def _group_out(
    group: Group,
    membership: UserGroup,
    member_count: int,
    invite: GroupInvite | None,
) -> GroupOut:
    is_admin = membership.role == GroupRole.admin.value
    can_see_invite = is_admin or group.invite_visible_to_members
    return GroupOut(
        id=group.id,
        name=group.name,
        my_role=membership.role,
        member_count=member_count,
        invite_visible_to_members=group.invite_visible_to_members,
        invite_token=(invite.token if invite and can_see_invite else None),
        created_at=group.created_at,
    )


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_private_group(
    request: Request,
    body: GroupCreateIn,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupOut:
    try:
        group, membership, invite = await create_group(session, creator=user, name=body.name)
        return _group_out(group, membership, member_count=1, invite=invite)
    except PrivateGroupError as exc:
        raise _group_error_to_http(exc) from exc


@router.post("/join", response_model=GroupOut)
@limiter.limit("30/minute")
async def join_private_group(
    request: Request,
    body: GroupJoinIn,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupOut:
    try:
        group, membership = await join_group_by_invite_token(
            session,
            user=user,
            invite_token=body.invite_token,
        )
        _, _, members, invite = await get_group_detail(session, group_id=group.id, user=user)
        return _group_out(group, membership, len(members), invite)
    except PrivateGroupError as exc:
        raise _group_error_to_http(exc) from exc


@router.get("", response_model=list[GroupOut])
async def list_my_groups(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> list[GroupOut]:
    rows = await list_user_groups(session, user=user)
    return [_group_out(g, m, c, inv) for g, m, c, inv in rows]


@router.get("/{group_id}", response_model=GroupDetailOut)
async def get_private_group(
    group_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupDetailOut:
    try:
        group, membership, members, invite = await get_group_detail(
            session,
            group_id=group_id,
            user=user,
        )
        member_outs = [
            GroupMemberOut(
                user_id=m.user_id,
                full_name=m.user.full_name if m.user else None,
                role=m.role,
                joined_at=m.joined_at,
            )
            for m in members
        ]
        base = _group_out(group, membership, len(member_outs), invite)
        return GroupDetailOut(**base.model_dump(), members=member_outs)
    except PrivateGroupError as exc:
        raise _group_error_to_http(exc) from exc


@router.post("/{group_id}/regenerate-invite", response_model=GroupInviteOut)
@limiter.limit("10/minute")
async def regenerate_group_invite(
    request: Request,
    group_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupInviteOut:
    try:
        invite = await regenerate_invite_token(session, group_id=group_id, actor=user)
        return GroupInviteOut(group_id=group_id, invite_token=invite.token)
    except PrivateGroupError as exc:
        raise _group_error_to_http(exc) from exc


@router.post("/{group_id}/members/{target_user_id}/promote", response_model=GroupMemberOut)
@limiter.limit("20/minute")
async def promote_group_member(
    request: Request,
    group_id: int,
    target_user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupMemberOut:
    try:
        membership = await promote_member_to_admin(
            session,
            group_id=group_id,
            actor=user,
            target_user_id=target_user_id,
        )
        await session.refresh(membership, attribute_names=["user"])
        return GroupMemberOut(
            user_id=membership.user_id,
            full_name=membership.user.full_name if membership.user else None,
            role=membership.role,
            joined_at=membership.joined_at,
        )
    except PrivateGroupError as exc:
        raise _group_error_to_http(exc) from exc


@router.patch("/{group_id}/settings", response_model=GroupOut)
@limiter.limit("20/minute")
async def patch_group_settings(
    request: Request,
    group_id: int,
    body: GroupSettingsUpdateIn,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupOut:
    try:
        await update_group_settings(
            session,
            group_id=group_id,
            actor=user,
            invite_visible_to_members=body.invite_visible_to_members,
        )
        group, membership, members, invite = await get_group_detail(
            session,
            group_id=group_id,
            user=user,
        )
        return _group_out(group, membership, len(members), invite)
    except PrivateGroupError as exc:
        raise _group_error_to_http(exc) from exc
