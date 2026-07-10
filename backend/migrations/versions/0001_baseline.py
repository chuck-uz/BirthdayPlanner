"""baseline schema (users, wishlists, subscriptions, admin_birthday_prompts, birthday_events)

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-10

Полная текущая схема одним ревизионным шагом.

ВАЖНО для уже работающих БД (таблицы созданы прежним create_all):
выполните `alembic stamp head` вместо `upgrade`, чтобы пометить схему как актуальную
без повторного CREATE TABLE. Свежая БД поднимается обычным `alembic upgrade head`.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=512), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("avatar_path", sa.String(length=512), nullable=True),
        sa.Column("is_bot_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_test", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "wishlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("link_url", sa.String(length=2048), nullable=True),
        sa.Column("photo_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

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


def downgrade() -> None:
    op.drop_table("birthday_events")
    op.drop_table("admin_birthday_prompts")
    op.drop_table("subscriptions")
    op.drop_table("wishlists")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
