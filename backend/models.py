from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    birth_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_bot_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )

    wishlists: Mapped[list[Wishlist]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Wishlist(Base):
    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
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
