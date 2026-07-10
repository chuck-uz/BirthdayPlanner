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
    is_bot_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
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


class Subscription(Base):
    """Подписка: subscriber хочет уведомления о ДР target_user."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("subscriber_id", "target_user_id", name="uq_subscription_subscriber_target"),
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


class AdminBirthdayPrompt(Base):
    """Запрос админу: создать группу вручную за N дней до ДР (состояние до BirthdayEvent)."""

    __tablename__ = "admin_birthday_prompts"
    __table_args__ = (
        UniqueConstraint("target_user_id", "celebration_date", name="uq_admin_prompt_target_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    celebration_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    # prompt_sent | create_selected | skipped | completed
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # Кому ушло сообщение с кнопками (админ из env или подписчик, если TELEGRAM_ADMIN_ID не задан)
    prompt_recipient_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    admin_prompt_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Полученная от оператора ссылка на группу (ждёт нажатия «Разослать»); переживает рестарт.
    pending_invite_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    target_user: Mapped[User] = relationship(foreign_keys=[target_user_id])


class BirthdayEvent(Base):
    """Один обработанный цикл ДР: группа/рассылка уже созданы, повтор не нужен."""

    __tablename__ = "birthday_events"
    __table_args__ = (
        UniqueConstraint("target_user_id", "celebration_date", name="uq_birthday_event_target_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    celebration_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    invite_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    used_dm_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)
    processed_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    target_user: Mapped[User] = relationship(foreign_keys=[target_user_id])


class Group(Base):
    """Приватная группа с ролями admin/member и инвайт-ссылками."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    invite_visible_to_members: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
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


class GroupBirthdayNotification(Base):
    """Idempotency для Telegram-уведомлений о ДР внутри приватной группы."""

    __tablename__ = "group_birthday_notifications"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "birthday_user_id",
            "celebration_date",
            "notification_kind",
            name="uq_group_bday_notify",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    birthday_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    celebration_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    notification_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
