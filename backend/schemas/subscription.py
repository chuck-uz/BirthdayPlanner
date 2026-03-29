from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramDeliveryOut(BaseModel):
    """Состояние доставки личных сообщений от бота текущему пользователю."""

    can_receive_bot_messages: bool
    bot_username: str | None = None


class SubscriptionStateOut(BaseModel):
    subscribed: bool
    can_receive_bot_messages: bool = Field(
        ...,
        description="Пользователь нажал /start у бота — можно слать личные уведомления",
    )
    bot_username: str | None = Field(
        default=None,
        description="Имя бота без @ для ссылки t.me/",
    )
