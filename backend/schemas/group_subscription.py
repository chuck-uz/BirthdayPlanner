from __future__ import annotations

from pydantic import BaseModel


class GroupSubscriptionStateOut(BaseModel):
    subscribed: bool
    can_subscribe: bool
