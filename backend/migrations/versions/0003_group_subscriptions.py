"""group-scoped subscriptions and birthday chat flow; drop legacy subscription system

Revision ID: 0003_group_subscriptions
Revises: 0002_private_groups
Create Date: 2026-07-11

Removes the platform-wide subscription system (subscriptions, admin_birthday_prompts,
birthday_events) and the informational-only group notification marker
(group_birthday_notifications) in favor of a group-scoped subscribe-to-a-groupmate
model with an interactive "create the Telegram chat" flow.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_group_subscriptions"
down_revision: Union[str, None] = "0002_private_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("group_birthday_notifications")
    op.drop_table("admin_birthday_prompts")
    op.drop_table("birthday_events")
    op.drop_table("subscriptions")

    op.add_column(
        "groups",
        sa.Column("notify_lead_days", sa.Integer(), server_default="7", nullable=False),
    )

    op.create_table(
        "group_member_subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subscriber_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["subscriber_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subscriber_id", "target_user_id", name="uq_group_member_sub_subscriber_target"
        ),
    )
    op.create_index(
        "ix_group_member_subscriptions_subscriber_id", "group_member_subscriptions", ["subscriber_id"]
    )
    op.create_index(
        "ix_group_member_subscriptions_target_user_id", "group_member_subscriptions", ["target_user_id"]
    )

    op.create_table(
        "group_birthday_prompts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("celebration_date", sa.Date(), nullable=False),
        sa.Column("state", sa.String(length=16), server_default="open", nullable=False),
        sa.Column("claimed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["claimed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id", "target_user_id", "celebration_date", name="uq_group_bday_prompt"
        ),
    )
    op.create_index("ix_group_birthday_prompts_group_id", "group_birthday_prompts", ["group_id"])
    op.create_index(
        "ix_group_birthday_prompts_target_user_id", "group_birthday_prompts", ["target_user_id"]
    )

    op.create_table(
        "group_birthday_prompt_recipients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=True),
        sa.Column("skipped", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["prompt_id"], ["group_birthday_prompts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prompt_id", "user_id", name="uq_group_bday_prompt_recipient"),
    )
    op.create_index(
        "ix_group_birthday_prompt_recipients_prompt_id", "group_birthday_prompt_recipients", ["prompt_id"]
    )
    op.create_index(
        "ix_group_birthday_prompt_recipients_user_id", "group_birthday_prompt_recipients", ["user_id"]
    )

    op.create_table(
        "group_birthday_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("celebration_date", sa.Date(), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("invite_link", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id", "target_user_id", "celebration_date", name="uq_group_bday_event"
        ),
    )
    op.create_index("ix_group_birthday_events_group_id", "group_birthday_events", ["group_id"])
    op.create_index(
        "ix_group_birthday_events_target_user_id", "group_birthday_events", ["target_user_id"]
    )


def downgrade() -> None:
    op.drop_table("group_birthday_events")
    op.drop_table("group_birthday_prompt_recipients")
    op.drop_table("group_birthday_prompts")
    op.drop_table("group_member_subscriptions")
    op.drop_column("groups", "notify_lead_days")

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subscriber_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["subscriber_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subscriber_id", "target_user_id", name="uq_subscription_subscriber_target"
        ),
    )
    op.create_index("ix_subscriptions_subscriber_id", "subscriptions", ["subscriber_id"])
    op.create_index("ix_subscriptions_target_user_id", "subscriptions", ["target_user_id"])

    op.create_table(
        "admin_birthday_prompts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("celebration_date", sa.Date(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("prompt_recipient_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("admin_prompt_message_id", sa.BigInteger(), nullable=True),
        sa.Column("pending_invite_link", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "target_user_id", "celebration_date", name="uq_admin_prompt_target_date"
        ),
    )
    op.create_index(
        "ix_admin_birthday_prompts_target_user_id", "admin_birthday_prompts", ["target_user_id"]
    )
    op.create_index("ix_admin_birthday_prompts_state", "admin_birthday_prompts", ["state"])

    op.create_table(
        "birthday_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("celebration_date", sa.Date(), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("invite_link", sa.String(length=512), nullable=True),
        sa.Column("used_dm_fallback", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("processed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "target_user_id", "celebration_date", name="uq_birthday_event_target_date"
        ),
    )
    op.create_index(
        "ix_birthday_events_target_user_id", "birthday_events", ["target_user_id"]
    )

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
