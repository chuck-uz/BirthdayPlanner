from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class GroupCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class GroupJoinIn(BaseModel):
    invite_token: str = Field(..., min_length=1)


class GroupSettingsUpdateIn(BaseModel):
    invite_visible_to_members: bool


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    my_role: str
    member_count: int
    invite_visible_to_members: bool
    invite_token: str | None = None
    created_at: dt.datetime


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str | None
    role: str
    joined_at: dt.datetime


class GroupDetailOut(GroupOut):
    members: list[GroupMemberOut]


class GroupInviteOut(BaseModel):
    group_id: int
    invite_token: str


class GroupBirthdayMemberOut(BaseModel):
    user_id: int
    full_name: str | None
    birth_date: dt.date
    days_until: int
    has_avatar: bool = False


class GroupBirthdaySectionOut(BaseModel):
    group_id: int
    group_name: str
    members: list[GroupBirthdayMemberOut]
