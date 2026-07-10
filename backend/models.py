from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class GroupRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    birth_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_bot_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_test: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    wishlists: Mapped[list[Wishlist]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    group_memberships: Mapped[list[UserGroup]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Wishlist(Base):
    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="wishlists")


class Group(Base):
    """Приватная группа с ролями admin/member и инвайт-ссылками."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    invite_visible_to_members: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # За сколько дней до ДР участника уведомлять админов группы; настраивается самой группой.
    notify_lead_days: Mapped[int] = mapped_column(nullable=False, default=7, server_default="7")
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    memberships: Mapped[list[UserGroup]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    invites: Mapped[list[GroupInvite]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )


class GroupInvite(Base):
    """Инвайт-ссылка группы. Не более одной активной (revoked_at IS NULL) на группу."""

    __tablename__ = "group_invites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[dt.datetime | None] = mapped_column(nullable=True)

    group: Mapped[Group] = relationship(back_populates="invites")


class UserGroup(Base):
    """Связь пользователя с группой и ролью (admin/member). Одна строка на пару."""

    __tablename__ = "user_groups"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group_user_group"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    joined_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="group_memberships")
    group: Mapped[Group] = relationship(back_populates="memberships")


class GroupMemberSubscription(Base):
    """Подписка на ДР конкретного человека, с которым есть общая группа.

    Не привязана к конкретной группе в хранении — актуальность (кому в итоге
    уйдёт рассылка) определяется текущим членством на момент события, а не
    членством на момент подписки.
    """

    __tablename__ = "group_member_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_id", "target_user_id", name="uq_group_member_sub_subscriber_target"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subscriber_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    subscriber: Mapped[User] = relationship(foreign_keys=[subscriber_id])
    target_user: Mapped[User] = relationship(foreign_keys=[target_user_id])


class GroupBirthdayPrompt(Base):
    """Открытый запрос "создать чат в Telegram" по ДР участника группы.

    Уходит нескольким получателям сразу (все админы группы, либо все
    участники в fallback-сценарии единственного админа); кто первый нажал
    «Создать» и добавил бота в группу — тот и закрывает событие.
    """

    __tablename__ = "group_birthday_prompts"
    __table_args__ = (
        UniqueConstraint(
            "group_id", "target_user_id", "celebration_date", name="uq_group_bday_prompt"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    celebration_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    # open | claimed | completed
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="open", server_default="open")
    claimed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    recipients: Mapped[list[GroupBirthdayPromptRecipient]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )


class GroupBirthdayPromptRecipient(Base):
    """Один получатель открытого промпта — своё сообщение с кнопками в личке."""

    __tablename__ = "group_birthday_prompt_recipients"
    __table_args__ = (
        UniqueConstraint("prompt_id", "user_id", name="uq_group_bday_prompt_recipient"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("group_birthday_prompts.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    prompt: Mapped[GroupBirthdayPrompt] = relationship(back_populates="recipients")


class GroupBirthdayEvent(Base):
    """Терминальная запись: для этого ДР в этой группе чат уже создан."""

    __tablename__ = "group_birthday_events"
    __table_args__ = (
        UniqueConstraint(
            "group_id", "target_user_id", "celebration_date", name="uq_group_bday_event"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    celebration_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    invite_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
