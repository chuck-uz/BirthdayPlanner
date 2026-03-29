from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WishlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: dt.datetime


class WishlistCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v
