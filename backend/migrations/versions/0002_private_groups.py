"""private groups (groups, group_invites, user_groups, group_birthday_notifications)

Revision ID: 0002_private_groups
Revises: 0001_baseline
Create Date: 2026-07-10
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_private_groups"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "invite_visible_to_members", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "group_invites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_group_invites_group_id", "group_invites", ["group_id"])
    op.create_index("ix_group_invites_token", "group_invites", ["token"], unique=True)

    op.create_table(
        "user_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "group_id", name="uq_user_group_user_group"),
    )
    op.create_index("ix_user_groups_user_id", "user_groups", ["user_id"])
    op.create_index("ix_user_groups_group_id", "user_groups", ["group_id"])
    op.create_index("ix_user_groups_role", "user_groups", ["role"])

    op.create_table(
        "group_birthday_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("birthday_user_id", sa.Integer(), nullable=False),
        sa.Column("celebration_date", sa.Date(), nullable=False),
        sa.Column("notification_kind", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["birthday_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id",
            "birthday_user_id",
            "celebration_date",
            "notification_kind",
            name="uq_group_bday_notify",
        ),
    )
    op.create_index(
        "ix_group_birthday_notifications_group_id", "group_birthday_notifications", ["group_id"]
    )
    op.create_index(
        "ix_group_birthday_notifications_birthday_user_id",
        "group_birthday_notifications",
        ["birthday_user_id"],
    )


def downgrade() -> None:
    op.drop_table("group_birthday_notifications")
    op.drop_table("user_groups")
    op.drop_table("group_invites")
    op.drop_table("groups")
